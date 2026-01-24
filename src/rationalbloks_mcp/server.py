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
import json
import os
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel.server import NotificationOptions
from mcp.types import Tool, TextContent

from .client import RationalBloksClient
from .tools import TOOLS

__version__ = "0.1.0"


# ============================================================================
# MCP SERVER CLASS
# ============================================================================

class RationalBloksMCPServer:
    """RationalBloks MCP Server - Backend as a Service for AI Agents."""
    
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required")
        if not api_key.startswith("rb_sk_"):
            raise ValueError("Invalid API key format - must start with 'rb_sk_'")
            
        self.api_key = api_key
        self.client = RationalBloksClient(api_key)
        self.server = Server("rationalbloks")
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Register MCP protocol handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
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
                result = self.client.execute(name, arguments)
                
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
    # HTTP TRANSPORT - Cloud/Smithery Deployment
    # ========================================================================
    
    def _run_http(self):
        """Run in HTTP mode for Smithery and cloud agents."""
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route, Mount
        from starlette.responses import Response, JSONResponse
        import uvicorn
        
        sse = SseServerTransport("/messages/")
        
        async def handle_sse(request):
            """SSE endpoint for MCP protocol."""
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await self.server.run(streams[0], streams[1], self._get_init_options())
            return Response()
        
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
        
        app = Starlette(
            debug=False,
            routes=[
                Route("/.well-known/mcp/server-card.json", endpoint=server_card, methods=["GET"]),
                Route("/health", endpoint=health, methods=["GET"]),
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ]
        )
        
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("HOST", "0.0.0.0")
        
        print(f"[rationalbloks-mcp] HTTP server starting on {host}:{port}", file=sys.stderr)
        uvicorn.run(app, host=host, port=port, log_level="info")


