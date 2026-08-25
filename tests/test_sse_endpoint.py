# ============================================================================
# SSE TRANSPORT TEST — /sse emits the `endpoint` event on connect
# ============================================================================
# Guards the bug class where /sse opens a 200 text/event-stream but never speaks
# the MCP SSE protocol: without an `event: endpoint` frame on connect, a legacy
# client has nowhere to POST `initialize`, so it hangs then times out. A health
# check that only asserts HTTP 200 is blind to this — so this test drives the ASGI
# app directly and asserts the protocol frame itself is emitted, fast.
#
# We drive the raw ASGI app (not an HTTP client): the SSE stream never ends, so we
# must control `receive` to disconnect the instant the frame lands — that lets the
# server tear the session down and the app coroutine return cleanly.
# ============================================================================

import asyncio
import contextlib

from rationalbloks_mcp.backend import create_backend_server
from rationalbloks_mcp.core.transport import create_http_app


def test_sse_emits_endpoint_event():
    # Outer timeout is a hard ceiling: a regressed /sse that never emits the frame
    # FAILS (below) instead of hanging the suite.
    asyncio.run(asyncio.wait_for(_probe_sse_endpoint_event(), timeout=15.0))


async def _probe_sse_endpoint_event() -> None:
    # http_mode=True builds the server with no startup key (auth is per-request); the
    # SSE handshake is transport-level, so it needs no backend and no valid key.
    server = create_backend_server(api_key=None, http_mode=True)
    app = create_http_app(
        server.server,
        server.name,
        server.version,
        server.instructions,
        server.get_init_options(),
    )

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/sse",
        "raw_path": b"/sse",
        "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"mcp.test"), (b"accept", b"text/event-stream")],
        "server": ("mcp.test", 80),
        "client": ("127.0.0.1", 12345),
    }

    endpoint_seen = asyncio.Event()
    disconnect = asyncio.Event()

    async def receive():
        # Hold the connection open until the frame lands, then disconnect so the
        # SSE transport tears down and the app coroutine returns.
        await disconnect.wait()
        return {"type": "http.disconnect"}

    async def send(message):
        if message["type"] == "http.response.body":
            body = message.get("body", b"")
            if b"event: endpoint" in body or b"event:endpoint" in body:
                endpoint_seen.set()
                disconnect.set()

    app_task = asyncio.ensure_future(app(scope, receive, send))
    try:
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(endpoint_seen.wait(), timeout=5.0)
    finally:
        disconnect.set()
        with contextlib.suppress(Exception):
            await asyncio.wait_for(app_task, timeout=5.0)

    assert endpoint_seen.is_set(), "SSE stream opened but never emitted an `event: endpoint` frame"
