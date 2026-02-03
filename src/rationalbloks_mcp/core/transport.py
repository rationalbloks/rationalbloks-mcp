# ============================================================================
# RATIONALBLOKS MCP - TRANSPORT LAYER
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Shared transport implementations for STDIO and HTTP modes.
# Both Backend and Frontend MCP use these exact same transport functions.
#
# DUAL TRANSPORT ARCHITECTURE:
# - STDIO:  Local development (Cursor, VS Code, Claude Desktop)
# - HTTP:   Cloud deployment (Smithery, Replit, web agents)
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
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

# Public API
__all__ = [
    "run_stdio",
    "run_http",
    "create_http_app",
]


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
    # Run MCP server in HTTP mode for cloud deployment
    # Used by: Smithery, Replit, web agents, cloud platforms
    # CHAIN: Build app → run uvicorn → no branching
    import uvicorn
    
    app = create_http_app(server, name, version, description, server_card_builder)
    
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    print(f"[rationalbloks-mcp] HTTP server starting on {host}:{port}", file=sys.stderr)
    print(f"[rationalbloks-mcp] MCP endpoints:", file=sys.stderr)
    print(f"[rationalbloks-mcp]   - http://{host}:{port}/sse (primary)", file=sys.stderr)
    print(f"[rationalbloks-mcp]   - http://{host}:{port}/mcp (alternative)", file=sys.stderr)
    
    uvicorn.run(app, host=host, port=port, log_level="info")


def create_http_app(
    server: Server,
    name: str,
    version: str,
    description: str,
    server_card_builder: Callable[[], dict] | None = None,
) -> Any:
    # Create Starlette ASGI application for HTTP transport
    # Returns fully configured ASGI app with:
    # - Server card endpoint (/.well-known/mcp/server-card.json)
    # - Health check endpoint (/health)
    # - MCP SSE endpoints (/sse, /mcp, /)
    # - CORS middleware for browser clients
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.responses import JSONResponse
    from starlette.middleware.cors import CORSMiddleware
    from starlette.types import Receive, Scope, Send
    
    # Create session manager for Streamable HTTP
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
    
    async def handle_streamable(scope: Scope, receive: Receive, send: Send):
        # Handle Streamable HTTP requests for MCP protocol
        await session_manager.handle_request(scope, receive, send)
    
    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        # Application lifespan for session manager
        async with session_manager.run():
            yield
    
    # Build Starlette app
    app = Starlette(
        debug=False,
        routes=[
            Route("/.well-known/mcp/server-card.json", endpoint=server_card, methods=["GET"]),
            Route("/health", endpoint=health, methods=["GET"]),
            Mount("/sse", app=handle_streamable),
            Mount("/mcp", app=handle_streamable),
            Mount("/", app=handle_streamable),
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
        "icon": "https://rationalbloks.com/logo.svg",
        "documentation": "https://rationalbloks.com/docs/mcp",
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
                },
                "mode": {
                    "type": "string",
                    "title": "Mode",
                    "description": "MCP mode: backend, frontend, or full (default: full)",
                    "default": "full",
                    "enum": ["backend", "frontend", "full"]
                }
            }
        }
    }
