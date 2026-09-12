# ============================================================================
# HTTP ROUTING TEST - the MCP endpoint answers, unknown paths are refused
# ============================================================================
# Guards two failure classes that a unit test on the handlers cannot see, both of
# which have actually shipped here.
#
# 1. An unknown path handed to the streamable session manager is never answered: the
#    connection is held open until the client gives up. Clients probe
#    /.well-known/oauth-protected-resource on connect (RFC 9728), so a hang there
#    stalls the connection instead of completing it.
# 2. Guarding against (1) with the wrong path form refuses the endpoint itself.
#    Starlette's Mount does not strip its prefix from scope["path"], so a handler
#    mounted at /mcp sees "/mcp"; a guard written for the stripped form 404s every
#    real request.
#
# Both are routing facts, invisible to anything that does not drive the ASGI app, so
# this test drives it. No backend call is made: initialize is served by the SDK from
# the local registry.
# ============================================================================

import pytest
from starlette.testclient import TestClient

from rationalbloks_mcp.backend import create_backend_server
from rationalbloks_mcp.core.transport import create_http_app

# Paths that must reach the session manager rather than the 404 guard.
ENDPOINT_PATHS = ["/mcp", "/"]

# Paths below a mount point, plus the transport we removed and the OAuth probe.
UNKNOWN_PATHS = [
    "/sse",
    "/messages/",
    "/mcp/foo",
    "/zzz",
    "/.well-known/oauth-protected-resource",
]

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


@pytest.fixture(scope="module")
def client():
    # http_mode means the key rides each request, so none is needed to build the app.
    server = create_backend_server(api_key=None, http_mode=True)
    app = create_http_app(
        server.server, server.name, server.version, server.instructions
    )
    # The context manager runs the lifespan, which starts the session manager.
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.parametrize("path", ENDPOINT_PATHS)
def test_mcp_endpoint_is_served(client, path):
    # A 404 here means the guard is refusing the endpoint it exists to protect.
    response = client.post(
        path,
        json=INITIALIZE,
        headers={"Accept": "application/json, text/event-stream"},
    )
    assert response.status_code != 404, f"{path} was refused by the route guard"
    assert response.status_code == 200, f"{path} returned {response.status_code}"
    assert "result" in response.json(), f"{path} did not answer initialize"


@pytest.mark.parametrize("path", UNKNOWN_PATHS)
def test_unknown_path_is_refused_not_held_open(client, path):
    # The assertion is that a response arrives at all AND that it is a refusal. A
    # regression here shows up as a hang, which the test runner surfaces as a timeout.
    assert client.get(path).status_code == 404, f"{path} should be 404"


def test_health_and_server_card_answer(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    card = client.get("/.well-known/mcp/server-card.json")
    assert card.status_code == 200
    assert card.json()["name"], "server card carries no name"
