# ============================================================================
# TOOL LIST — tools/list offers the gateway's tools, as the request's key may call them
# ============================================================================
# The package keeps no copy of a tool: on every tools/list it lists what the gateway
# serves (GET /api/mcp/tools), with the request's key, so a read key's server lists the
# read tools alone and a client allows all of it with one rule. A request without a key
# lists every tool the gateway serves without one: it can call none of them, and a
# directory reads the catalog that way. A refused key fails the list with the gateway's
# reason instead of listing tools that all fail. The gateway is replaced by a stub of
# LogicBlokClient.list_tools; no backend call is made.
# ============================================================================

import asyncio
from types import SimpleNamespace

import pytest
from mcp.types import INTERNAL_ERROR
from starlette.testclient import TestClient

from rationalbloks_mcp.backend import create_backend_server
from rationalbloks_mcp.backend.client import LogicBlokClient
from rationalbloks_mcp.core.auth import stdio_api_key
from rationalbloks_mcp.core.transport import create_http_app

KEY = "rb_sk_" + "0" * 40

# No request on STDIO: the server reads the key it started with
STDIO_CONTEXT = SimpleNamespace(request=None)


def tool(name: str, read: bool) -> dict:
    # One tool as the gateway serves it (logicblok/mcp_gateway.py, mcp_tool)
    return {"name": name, "title": name.replace("_", " ").title(), "group": "Relational Tools",
            "description": f"The {name} tool", "inputSchema": {"type": "object", "properties": {}, "required": []},
            "annotations": {"readOnlyHint": read, "destructiveHint": False, "idempotentHint": read, "openWorldHint": False}}


READ_TOOLS = [tool("list_projects", True), tool("get_schema", True)]
EVERY_TOOL = READ_TOOLS + [tool("deploy_staging", False)]

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


def answering(monkeypatch, keyed, keyless=EVERY_TOOL) -> list:
    # Stub the gateway's tool list: `keyed` (a list of tools, or an exception to raise) for a client with a
    # key, `keyless` for one without; returns the keys it was asked with
    asked = []

    async def list_tools(self):
        asked.append(self.api_key)
        answer = keyed if self.api_key else keyless
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(LogicBlokClient, "list_tools", list_tools)
    return asked


def listed_over_http(headers: dict) -> dict:
    # The hosted server's JSON-RPC answer to tools/list, sent with these headers
    server = create_backend_server(api_key=None, http_mode=True)
    app = create_http_app(server.server, server.name, server.version, server.INSTRUCTIONS)
    with TestClient(app) as client:
        client.post("/mcp", json=INITIALIZE, headers=headers)
        return client.post("/mcp", json=LIST_TOOLS, headers=headers).json()


def test_a_key_lists_only_the_tools_it_may_call(monkeypatch):
    asked = answering(monkeypatch, READ_TOOLS)
    answer = listed_over_http({**HEADERS, "Authorization": f"Bearer {KEY}"})
    assert [tool["name"] for tool in answer["result"]["tools"]] == ["list_projects", "get_schema"]
    assert asked == [KEY]


def test_a_request_without_a_key_lists_every_tool_the_gateway_serves(monkeypatch):
    asked = answering(monkeypatch, READ_TOOLS)
    answer = listed_over_http(HEADERS)
    assert [tool["name"] for tool in answer["result"]["tools"]] == [tool["name"] for tool in EVERY_TOOL]
    assert asked == [None]


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
    assert [tool.name for tool in tools] == ["list_projects", "get_schema"]
    assert asked == [KEY]


def test_a_stdio_server_without_a_key_lists_every_tool_with_its_hints_and_each_call_says_how_to_set_it(monkeypatch):
    answering(monkeypatch, READ_TOOLS)
    server = create_backend_server(api_key=None, http_mode=False)
    handlers = server._build_handlers()
    tools = asyncio.run(handlers["on_list_tools"](STDIO_CONTEXT, None)).tools

    # Each listed tool carries what the gateway served, the hints a client decides by included
    served = {tool.name: (tool.title, tool.description, tool.annotations.model_dump(by_alias=True, exclude_none=True))
              for tool in tools}
    assert served == {tool["name"]: (tool["title"], tool["description"], tool["annotations"]) for tool in EVERY_TOOL}

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
