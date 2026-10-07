# ============================================================================
# TOOL LIST — tools/list offers what the request's key may call
# ============================================================================
# The server lists the tools the gateway answers the key may call (GET
# /api/mcp/allowed-tools), so a read key's server lists the read tools alone and a
# client allows all of it with one rule. A request without a key lists every tool: it
# can call none of them, and a directory reads the catalog that way. A refused key
# fails the list with the gateway's reason instead of listing tools that all fail.
# The gateway is replaced by a stub of LogicBlokClient.allowed_tools; no backend call
# is made.
# ============================================================================

import asyncio
from types import SimpleNamespace

import pytest
from mcp.types import INTERNAL_ERROR
from starlette.testclient import TestClient

from rationalbloks_mcp.backend import INFRASTRUCTURE_TOOLS, create_backend_server
from rationalbloks_mcp.backend.client import LogicBlokClient
from rationalbloks_mcp.core.auth import stdio_api_key
from rationalbloks_mcp.core.transport import create_http_app

KEY = "rb_sk_" + "0" * 40
READ_TOOLS = ["list_projects", "get_schema", "get_job_status"]

HEADERS = {"Accept": "application/json, text/event-stream", "MCP-Protocol-Version": "2025-06-18"}
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1"},
    },
}
LIST_TOOLS = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

# No request on STDIO: the server reads the key it started with
STDIO_CONTEXT = SimpleNamespace(request=None)

# The annotations a tool listing carries
HINTS = {"readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"}


def answering(monkeypatch, answer) -> list:
    # Stub the gateway's tool list with answer (a list of names, or an exception to raise),
    # returning the keys it was asked with
    asked = []

    async def allowed_tools(self):
        asked.append(self.api_key)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(LogicBlokClient, "allowed_tools", allowed_tools)
    return asked


def listed_over_http(headers: dict) -> dict:
    # The hosted server's JSON-RPC answer to tools/list, sent with these headers
    server = create_backend_server(api_key=None, http_mode=True)
    app = create_http_app(server.server, server.name, server.version, server.instructions)
    with TestClient(app) as client:
        client.post("/mcp", json=INITIALIZE, headers=headers)
        return client.post("/mcp", json=LIST_TOOLS, headers=headers).json()


def test_a_key_lists_only_the_tools_it_may_call(monkeypatch):
    asked = answering(monkeypatch, READ_TOOLS)
    answer = listed_over_http({**HEADERS, "Authorization": f"Bearer {KEY}"})
    assert sorted(tool["name"] for tool in answer["result"]["tools"]) == sorted(READ_TOOLS)
    assert asked == [KEY]


def test_a_request_without_a_key_lists_every_tool(monkeypatch):
    asked = answering(monkeypatch, READ_TOOLS)
    answer = listed_over_http(HEADERS)
    assert len(answer["result"]["tools"]) == len(INFRASTRUCTURE_TOOLS)
    assert asked == [], "a request without a key asked the gateway for its tools"


def test_a_refused_key_fails_the_list_with_the_gateway_reason(monkeypatch):
    reason = "RationalBloks answered 401 to the tool list: Invalid API key"
    answering(monkeypatch, Exception(reason))
    answer = listed_over_http({**HEADERS, "Authorization": f"Bearer {KEY}"})
    assert "result" not in answer
    assert answer["error"] == {"code": INTERNAL_ERROR, "message": reason}


def test_a_stdio_key_lists_only_the_tools_it_may_call(monkeypatch):
    asked = answering(monkeypatch, READ_TOOLS)
    server = create_backend_server(api_key=KEY, http_mode=False)
    on_list_tools = server._build_handlers()["on_list_tools"]
    tools = asyncio.run(on_list_tools(STDIO_CONTEXT, None)).tools
    assert sorted(tool.name for tool in tools) == sorted(READ_TOOLS)
    assert asked == [KEY]


def test_a_stdio_server_without_a_key_lists_every_tool_and_each_call_says_how_to_set_it():
    server = create_backend_server(api_key=None, http_mode=False)
    handlers = server._build_handlers()
    tools = asyncio.run(handlers["on_list_tools"](STDIO_CONTEXT, None)).tools
    assert len(tools) == len(INFRASTRUCTURE_TOOLS)

    # Each listed tool carries the hints its catalog entry states, the ones a client decides by
    served = {tool.name: {hint: value for hint, value in tool.annotations.model_dump(by_alias=True).items()
                          if hint in HINTS} for tool in tools}
    assert served == {tool["name"]: tool["annotations"] for tool in INFRASTRUCTURE_TOOLS}

    call = SimpleNamespace(name="list_projects", arguments={})
    result = asyncio.run(handlers["on_call_tool"](STDIO_CONTEXT, call))
    assert result.is_error is True
    assert "set RATIONALBLOKS_API_KEY" in result.content[0].text


def test_the_stdio_key_is_checked_for_shape():
    assert stdio_api_key(None) is None
    assert stdio_api_key("") is None
    assert stdio_api_key(KEY) == KEY
    with pytest.raises(ValueError, match="starts with 'rb_sk_'"):
        stdio_api_key("sk_live_not_a_rationalbloks_key")
