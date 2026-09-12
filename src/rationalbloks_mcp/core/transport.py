# ============================================================================
# RATIONALBLOKS MCP - TRANSPORT LAYER
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Shared transport implementations for STDIO and HTTP modes.
# Backend MCP uses these transport functions for both local and cloud deployment.
#
# THE TWO TRANSPORTS THE MCP SPECIFICATION DEFINES:
# - STDIO:           the package run as a subprocess (Claude Desktop, Smithery)
# - Streamable HTTP: the hosted server (Claude Code, Cursor, GitHub Copilot, and
#                    anything else that takes a remote MCP server)
#
# CHAIN MANTRA: No branching, single path through each transport
# ============================================================================

import asyncio
import contextlib
import os
import sys
from typing import Any, Callable
from collections.abc import AsyncIterator

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

# Public API
__all__ = [
    "run_stdio",
    "run_http",
    "create_http_app",
]

# The paths that ARE the MCP endpoint, which is served at /mcp and at the origin.
# Starlette's Mount leaves scope["path"] as the full request path and records the
# matched prefix in root_path, so a handler mounted at /mcp sees "/mcp" here, not a
# stripped remainder. Anything not in this tuple reached a mount by falling past every
# named route, which makes it an unknown path.
MCP_ENDPOINT_PATHS = ("", "/", "/mcp", "/mcp/")


# ============================================================================
# STDIO TRANSPORT - Local IDE Integration
# ============================================================================

def run_stdio(
    server: Server,
    init_options: InitializationOptions,
) -> None:
    # Run MCP server in STDIO mode for local IDEs
    # Used by: Cursor, VS Code, Claude Desktop, Windsurf
    # CHAIN: Single async run, no error branching
    asyncio.run(_stdio_async(server, init_options))


async def _stdio_async(
    server: Server,
    init_options: InitializationOptions,
) -> None:
    # Async STDIO handler with MCP stream management
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)


# ============================================================================
# HTTP TRANSPORT - Cloud/Smithery Deployment
# ============================================================================

def run_http(
    server: Server,
    name: str,
    version: str,
    description: str,
    server_card_builder: Callable[[], dict] | None = None,
) -> None:
    # Run MCP server over Streamable HTTP for the hosted deployment
    # CHAIN: Build app → run uvicorn → no branching
    import uvicorn

    app = create_http_app(server, name, version, description, server_card_builder)

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"[rationalbloks-mcp] HTTP server starting on {host}:{port}", file=sys.stderr)
    print(f"[rationalbloks-mcp] MCP endpoint: http://{host}:{port}/mcp", file=sys.stderr)

    uvicorn.run(app, host=host, port=port, log_level="info")


def create_http_app(
    server: Server,
    name: str,
    version: str,
    description: str,
    server_card_builder: Callable[[], dict] | None = None,
) -> Any:
    # Create the Starlette ASGI application serving Streamable HTTP, the only transport
    # the MCP specification defines for a server reached over a network. It answers at
    # /mcp and at the origin itself, alongside the server card for discovery and /health
    # for the Kubernetes probes, with CORS so browser-based clients can connect.
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import JSONResponse
    from starlette.middleware.cors import CORSMiddleware
    from starlette.types import Receive, Scope, Send

    # Streamable HTTP (preferred) — one stateless session manager for /mcp and /.
    session_manager = StreamableHTTPSessionManager(
        app=server,
        json_response=True,
        stateless=True,
    )

    async def server_card(request):
        # MCP Server Card for Smithery discovery
        if server_card_builder:
            card = server_card_builder()
        else:
            card = _build_default_server_card(name, version, description)
        return JSONResponse(card)

    async def health(request):
        # Health check endpoint for Kubernetes probes
        return JSONResponse({"status": "ok", "version": version})

    async def handle_mcp(scope: Scope, receive: Receive, send: Send):
        # Streamable HTTP, mounted at /mcp and at the origin. Anything deeper than
        # either mount point is an unknown path: answer 404 instead of handing it to
        # the session manager, which holds the connection open until the client times
        # out. Clients probe /.well-known/oauth-* on connect (RFC 9728), so a hang there
        # stalls a connection that a refusal completes at once.
        if scope["path"] not in MCP_ENDPOINT_PATHS:
            await JSONResponse({"detail": "Not Found"}, status_code=404)(scope, receive, send)
            return
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        # Application lifespan for the Streamable HTTP session manager
        async with session_manager.run():
            yield

    # Route order: specific paths before the "/" catch-all (Starlette matches in order).
    app = Starlette(
        debug=False,
        routes=[
            Route("/.well-known/mcp/server-card.json", endpoint=server_card, methods=["GET"]),
            Route("/health", endpoint=health, methods=["GET"]),
            Mount("/mcp", app=handle_mcp),
            Mount("/", app=handle_mcp),
        ],
        lifespan=lifespan,
    )

    # Add CORS middleware
    app = CORSMiddleware(
        app,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],
    )

    return app


def _build_default_server_card(name: str, version: str, description: str) -> dict:
    # Build default MCP server card for Smithery
    return {
        "name": name,
        "displayName": "RationalBloks MCP",
        "version": version,
        "description": description,
        "vendor": "RationalBloks",
        "homepage": "https://rationalbloks.com",
        "icon": "https://rationalbloks.com/favicon.svg",
        "documentation": "https://rationalbloks.com/documentation",
        "capabilities": {
            "tools": True,
            "resources": True,
            "prompts": True
        },
        "authentication": {
            "type": "bearer",
            "scheme": "Bearer",
            "description": "RationalBloks API Key (format: rb_sk_...)",
            "header": "Authorization: Bearer rb_sk_..."
        },
        "configSchema": {
            "type": "object",
            "title": "RationalBloks Configuration",
            "required": [],
            "properties": {
                "apiKey": {
                    "type": "string",
                    "title": "API Key",
                    "description": "Your RationalBloks API key (get from https://rationalbloks.com/settings)",
                    "default": "",
                    "x-from": {"header": "authorization"}
                }
            }
        }
    }
