# ============================================================================
# RATIONALBLOKS MCP SERVER
# ============================================================================
# Copyright © 2026 RationalBloks. All Rights Reserved.
#
# Model Context Protocol (MCP) Server for AI Agent Communication
# Enables AI agents (Claude, Cursor, GPT, Windsurf) to build backends via chat
#
# DUAL TRANSPORT ARCHITECTURE:
# - STDIO:  Local development (Cursor, VS Code, Claude Desktop)
# - HTTP:   Cloud deployment (Smithery, Replit, web agents)
#
# ============================================================================

import asyncio
import contextlib
import json
import os
import sys
from typing import Any
from collections.abc import AsyncIterator

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel.server import NotificationOptions
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.types import Tool, TextContent
from starlette.requests import Request

from .client import RationalBloksClient
from .tools import TOOLS

__version__ = "0.1.3"


# ============================================================================
# MCP SERVER CLASS
# ============================================================================

class RationalBloksMCPServer:
    """RationalBloks MCP Server - Backend as a Service for AI Agents."""
    
    def __init__(self, api_key: str | None = None, http_mode: bool = False):
        """
        Initialize the MCP server.
        
        Args:
            api_key: Required for STDIO mode, optional for HTTP mode
            http_mode: If True, runs without requiring API key at startup
        """
        self.http_mode = http_mode
        
        if not http_mode:
            # STDIO mode requires API key at startup
            if not api_key:
                raise ValueError("API key is required")
            if not api_key.startswith("rb_sk_"):
                raise ValueError("Invalid API key format - must start with 'rb_sk_'")
            self.api_key = api_key
            self.client = RationalBloksClient(api_key)
        else:
            # HTTP mode - API key comes from request headers
            self.api_key = None
            self.client = None
            
        self.server = Server("rationalbloks")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Register MCP protocol handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            # Tools can be listed without auth - this is for discovery
            return [
                Tool(
                    name=tool["name"],
                    description=tool["description"],
                    inputSchema=tool["inputSchema"]
                )
                for tool in TOOLS
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            try:
                # Get client based on transport mode
                client = self._get_client_for_request()
                
                if client is None:
                    return [TextContent(
                        type="text", 
                        text="Error: API key required. Provide 'x-api-key' header with your RationalBloks API key (rb_sk_...)."
                    )]
                
                result = client.execute(name, arguments)
                
                if result.get("success"):
                    data = result.get("result", {})
                    formatted = json.dumps(data, indent=2, default=str)
                    return [TextContent(type="text", text=formatted)]
                else:
                    error = result.get("error", "Unknown error")
                    return [TextContent(type="text", text=f"Error: {error}")]
                    
            except Exception as e:
                print(f"[rationalbloks-mcp] Error: {e}", file=sys.stderr)
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _get_client_for_request(self) -> RationalBloksClient | None:
        """
        Get the appropriate client for the current request.
        
        - STDIO mode: Uses the pre-configured client with env API key
        - HTTP mode: Extracts API key from request headers per-request
        """
        if not self.http_mode:
            # STDIO mode - use pre-configured client
            return self.client
        
        # HTTP mode - extract API key from request headers
        try:
            ctx = self.server.request_context
            if ctx.request and isinstance(ctx.request, Request):
                # Get API key from x-api-key header
                api_key = ctx.request.headers.get("x-api-key")
                if api_key and api_key.startswith("rb_sk_"):
                    return RationalBloksClient(api_key)
        except (LookupError, AttributeError):
            # Context not available - not in a request
            pass
        
        return None
    
    def _get_init_options(self) -> InitializationOptions:
        """Get MCP initialization options."""
        return InitializationOptions(
            server_name="rationalbloks",
            server_version=__version__,
            capabilities=self.server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
        )
    
    def run(self, transport: str = "stdio"):
        """Run the MCP server with the specified transport."""
        if transport == "http":
            self._run_http()
        else:
            self._run_stdio()
    
    # ========================================================================
    # STDIO TRANSPORT - Local IDE Integration
    # ========================================================================
    
    def _run_stdio(self):
        """Run in STDIO mode for Cursor, VS Code, Claude Desktop."""
        asyncio.run(self._stdio_async())
    
    async def _stdio_async(self):
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self._get_init_options())
    
    # ========================================================================
    # HTTP TRANSPORT - Cloud/Smithery Deployment (Streamable HTTP)
    # ========================================================================
    
    def _run_http(self):
        """Run in HTTP mode for Smithery and cloud agents using Streamable HTTP."""
        from starlette.applications import Starlette
        from starlette.routing import Route, Mount
        from starlette.responses import JSONResponse
        from starlette.middleware.cors import CORSMiddleware
        from starlette.types import Receive, Scope, Send
        import uvicorn
        
        # Create session manager for Streamable HTTP
        session_manager = StreamableHTTPSessionManager(
            app=self.server,
            json_response=True,  # Use JSON responses for compatibility
            stateless=True,  # Stateless for scalability
        )
        
        async def server_card(request):
            """MCP Server Card for Smithery discovery."""
            return JSONResponse({
                "name": "rationalbloks",
                "version": __version__,
                "description": "RationalBloks MCP Server - Backend as a Service for AI Agents",
                "vendor": "RationalBloks",
                "homepage": "https://rationalbloks.com",
                "capabilities": {"tools": True, "resources": False, "prompts": False},
                "authentication": {
                    "type": "header",
                    "header": "x-api-key",
                    "description": "RationalBloks API Key"
                }
            })
        
        async def health(request):
            """Health check for Kubernetes probes."""
            return JSONResponse({"status": "ok", "version": __version__})
        
        # The Streamable HTTP handler - it handles POST requests for JSON-RPC
        async def handle_streamable(scope: Scope, receive: Receive, send: Send):
            """Handle Streamable HTTP requests for MCP protocol."""
            await session_manager.handle_request(scope, receive, send)
        
        @contextlib.asynccontextmanager
        async def lifespan(app: Starlette) -> AsyncIterator[None]:
            async with session_manager.run():
                yield
        
        app = Starlette(
            debug=False,
            routes=[
                Route("/.well-known/mcp/server-card.json", endpoint=server_card, methods=["GET"]),
                Route("/health", endpoint=health, methods=["GET"]),
                # Mount session manager at root - handles POST to /
                Mount("/", app=handle_streamable),
            ],
            lifespan=lifespan,
        )
        
        # Add CORS middleware for browser-based clients
        app = CORSMiddleware(
            app,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["*"],
            expose_headers=["Mcp-Session-Id"],
        )
        
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("HOST", "0.0.0.0")
        
        print(f"[rationalbloks-mcp] Streamable HTTP server starting on {host}:{port}", file=sys.stderr)
        print(f"[rationalbloks-mcp] MCP endpoint: http://{host}:{port}/mcp", file=sys.stderr)
        uvicorn.run(app, host=host, port=port, log_level="info")


