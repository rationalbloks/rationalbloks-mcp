# ============================================================================
# RATIONALBLOKS MCP SERVER
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Model Context Protocol (MCP) Server for AI Agent Communication
# Enables AI agents (Claude, Cursor, GPT, Windsurf) to build backends via chat
#
# DUAL TRANSPORT ARCHITECTURE:
# - STDIO:  Local development (Cursor, VS Code, Claude Desktop)
# - HTTP:   Cloud deployment (Smithery, Replit, web agents)
#
# WHY THIS EXISTS:
# AI agents need a standard protocol to communicate with backend services.
# This server implements MCP (Model Context Protocol) to expose RationalBloks
# platform capabilities to any AI agent supporting MCP.
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
from mcp.types import (
    Tool,
    ToolAnnotations,
    TextContent,
    Prompt,
    PromptArgument,
    PromptMessage,
    GetPromptResult,
    Resource,
    Icon
)
from starlette.requests import Request

from .client import RationalBloksClient
from .tools import TOOLS

# Version - read dynamically to avoid circular import
try:
    from importlib.metadata import version as _get_version
    __version__ = _get_version("rationalbloks-mcp")
except Exception:
    __version__ = "0.1.10"


# ============================================================================
# STATIC RESOURCE CONTENT
# ============================================================================
# Pre-defined documentation content for MCP resources
# WHY: Extracted to constants for cleaner read_resource handler

DOCS_GETTING_STARTED = """# Getting Started with RationalBloks MCP

## Quick Start

1. Get your API key from https://rationalbloks.com/dashboard
2. Set environment variable: export RATIONALBLOKS_API_KEY=rb_sk_...
3. Run the server: uvx rationalbloks-mcp

## Create Your First Project

Use the create_project tool with a name and JSON schema.

## Need Help?

Visit https://rationalbloks.com/docs for full documentation.
"""

DOCS_SCHEMA_REFERENCE = """# RationalBloks Schema Reference

## Field Types

- string: Text fields
- integer: Whole numbers
- number: Decimal numbers
- boolean: True/false values
- array: Lists of items
- object: Nested structures

## Example Schema

{
  "tables": {
    "users": {
      "fields": {
        "name": {"type": "string"},
        "email": {"type": "string"}
      }
    }
  }
}
"""

DOCS_API_REFERENCE = """# RationalBloks MCP API Reference

## Read Tools
- list_projects: List all projects
- get_project: Get project details
- get_schema: Get project schema
- get_user_info: Get authenticated user info

## Write Tools
- create_project: Create new project
- update_schema: Update project schema
- deploy_staging: Deploy to staging
- deploy_production: Deploy to production
- delete_project: Delete a project

For full documentation, visit https://rationalbloks.com/docs
"""


# ============================================================================
# MCP SERVER CLASS
# ============================================================================

class RationalBloksMCPServer:
    # RationalBloks MCP Server - Backend as a Service for AI Agents
    # Implements Model Context Protocol with dual transport (STDIO + HTTP)
    
    def __init__(self, api_key: str | None = None, http_mode: bool = False) -> None:
        # Initialize MCP server with appropriate transport mode
        # 
        # STDIO mode: API key required at startup (from environment)
        # HTTP mode: API key extracted per-request from Authorization header
        #
        # Validation:
        # - API key must start with "rb_sk_" prefix
        # - STDIO mode fails fast if key missing or invalid
        # - HTTP mode defers validation to request time
        
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
        
        self.server = Server(
            name="rationalbloks",
            version=__version__,
            instructions="RationalBloks MCP Server - Enterprise Backend-as-a-Service for AI agents. Build production APIs from JSON schemas.",
            website_url="https://rationalbloks.com",
            icons=[
                Icon(src="https://rationalbloks.com/logo.svg", mimeType="image/svg+xml"),
                Icon(src="https://rationalbloks.com/logo.png", mimeType="image/png", sizes=["128x128"]),
            ],
        )
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        # Register all MCP protocol handlers
        # Single registration point for tools, prompts, resources
        # WHY: Centralizes handler registration for maintainability
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            # List all available MCP tools with schemas and annotations
            # Returns complete tool definitions including input schemas and hints
            # WHY: MCP discovery - clients need to know available operations and their behavior
            
            tools_list = []
            for tool in TOOLS:
                # Build ToolAnnotations if present in tool definition
                annotations = None
                if "annotations" in tool:
                    ann = tool["annotations"]
                    annotations = ToolAnnotations(
                        readOnlyHint=ann.get("readOnlyHint"),
                        destructiveHint=ann.get("destructiveHint"),
                        idempotentHint=ann.get("idempotentHint"),
                        openWorldHint=ann.get("openWorldHint")
                    )
                
                tool_obj = Tool(
                    name=tool["name"],
                    title=tool.get("title"),
                    description=tool["description"],
                    inputSchema=tool["inputSchema"],
                    annotations=annotations
                )
                tools_list.append(tool_obj)
            return tools_list
        
        @self.server.list_prompts()
        async def list_prompts() -> list[Prompt]:
            # List available prompts for common workflows
            # Provides pre-built workflows for typical tasks
            # WHY: Reduces cognitive load for AI agents by offering ready-made workflows
            
            return [
                Prompt(
                    name="create-crud-api",
                    description="Create a full CRUD API project from a data model description",
                    arguments=[
                        PromptArgument(
                            name="data_model",
                            description="Describe your data model (e.g., 'blog with posts, comments, users')",
                            required=True
                        )
                    ]
                ),
                Prompt(
                    name="deploy-project",
                    description="Deploy an existing project through staging to production",
                    arguments=[
                        PromptArgument(
                            name="project_name",
                            description="Name of the project to deploy",
                            required=True
                        )
                    ]
                ),
                Prompt(
                    name="check-project-status",
                    description="Get comprehensive status of a project including deployments and metrics",
                    arguments=[
                        PromptArgument(
                            name="project_name",
                            description="Name of the project to check",
                            required=True
                        )
                    ]
                )
            ]
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> GetPromptResult:
            # Get a specific prompt with populated content
            # Fills in workflow templates with user-provided arguments
            # WHY: Transforms generic workflows into executable instructions
            
            if name == "create-crud-api":
                data_model = (arguments or {}).get("data_model", "your data model")
                return GetPromptResult(
                    description="Create a full CRUD API from data model",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(
                                type="text",
                                text=f"Create a new RationalBloks project for: {data_model}. Include all necessary tables, fields, and relationships. Use create_project tool with appropriate schema."
                            )
                        )
                    ]
                )
            
            elif name == "deploy-project":
                project_name = (arguments or {}).get("project_name", "project")
                return GetPromptResult(
                    description="Deploy project workflow",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(
                                type="text",
                                text=f"Deploy {project_name}: 1) Use list_projects to find project_id, 2) Use deploy_staging, 3) Check get_job_status, 4) If staging works, use deploy_production"
                            )
                        )
                    ]
                )
            
            elif name == "check-project-status":
                project_name = (arguments or {}).get("project_name", "project")
                return GetPromptResult(
                    description="Comprehensive project status check",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(
                                type="text",
                                text=f"Check {project_name} status: 1) Use list_projects to get ID, 2) Use get_project_info for deployment status, 3) Use get_project_usage for metrics, 4) Use get_version_history for recent changes"
                            )
                        )
                    ]
                )
            
            raise ValueError(f"Unknown prompt: {name}")
        
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            # List available resources (project schemas and documentation)
            # Returns: Static docs + dynamic project resources if authenticated
            # WHY: Static resources ensure Smithery quality checks pass
            
            # Static resources - always available without auth
            resources = [
                Resource(
                    uri="rationalbloks://docs/getting-started",
                    name="Getting Started Guide",
                    description="Quick start guide for RationalBloks MCP server",
                    mimeType="text/markdown"
                ),
                Resource(
                    uri="rationalbloks://docs/schema-reference",
                    name="Schema Reference",
                    description="JSON schema format and field types reference",
                    mimeType="text/markdown"
                ),
                Resource(
                    uri="rationalbloks://docs/api-reference",
                    name="API Reference",
                    description="Complete MCP tool documentation",
                    mimeType="text/markdown"
                )
            ]
            
            # Dynamic project resources - requires authentication
            client = self._get_client_for_request()
            if client:
                try:
                    result = client.execute("list_projects", {})
                    if result.get("success"):
                        projects = result.get("result", {}).get("projects", [])
                        
                        for project in projects:
                            project_id = project.get("id", "")
                            project_name = project.get("name", "Unknown")
                            
                            # Schema resource
                            resources.append(Resource(
                                uri=f"rationalbloks://project/{project_id}/schema",
                                name=f"{project_name} - Schema",
                                description=f"JSON schema definition for {project_name}",
                                mimeType="application/json"
                            ))
                            
                            # Project info resource
                            resources.append(Resource(
                                uri=f"rationalbloks://project/{project_id}/info",
                                name=f"{project_name} - Info",
                                description=f"Deployment status and metadata for {project_name}",
                                mimeType="application/json"
                            ))
                except Exception:
                    # Fail silently for dynamic resources
                    # WHY: Static resources still available
                    pass
            
            return resources
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            # Read a specific resource by URI
            # Handles both static docs and dynamic project resources
            # WHY: Provides AI agents access to docs and project schemas
            
            # Static documentation resources - no auth required
            static_docs = {
                "rationalbloks://docs/getting-started": DOCS_GETTING_STARTED,
                "rationalbloks://docs/schema-reference": DOCS_SCHEMA_REFERENCE,
                "rationalbloks://docs/api-reference": DOCS_API_REFERENCE,
            }
            
            if uri in static_docs:
                return static_docs[uri]
            
            # Dynamic project resources - require authentication
            client = self._get_client_for_request()
            if not client:
                raise ValueError("Authentication required to read project resources")
            
            # Parse URI: rationalbloks://project/{id}/{type}
            if not uri.startswith("rationalbloks://project/"):
                raise ValueError(f"Invalid URI format: {uri}")
            
            parts = uri.replace("rationalbloks://project/", "").split("/")
            if len(parts) != 2:
                raise ValueError(f"Invalid URI format: {uri}")
            
            project_id, resource_type = parts
            
            if resource_type == "schema":
                result = client.execute("get_schema", {"project_id": project_id})
            elif resource_type == "info":
                result = client.execute("get_project_info", {"project_id": project_id})
            else:
                raise ValueError(f"Unknown resource type: {resource_type}")
            
            if result.get("success"):
                return json.dumps(result.get("result", {}), indent=2)
            else:
                raise ValueError(result.get("error", "Failed to read resource"))
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            # Execute a tool with provided arguments
            # Single code path: get client → execute → format response
            # WHY: Core MCP operation - all tool invocations flow through here
            
            try:
                client = self._get_client_for_request()
                
                if client is None:
                    return [TextContent(
                        type="text",
                        text="Error: API key required. Provide 'Authorization: Bearer rb_sk_...' header with your RationalBloks API key."
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
        # Get the appropriate client for the current request
        # STDIO mode: Returns pre-configured client with environment API key
        # HTTP mode: Extracts API key from Authorization Bearer header per-request
        # WHY: Dual transport requires different authentication strategies
        
        if not self.http_mode:
            return self.client
        
        # HTTP mode - extract API key from Authorization: Bearer header
        try:
            ctx = self.server.request_context
            if ctx.request and isinstance(ctx.request, Request):
                auth_header = ctx.request.headers.get("authorization", "")
                if auth_header.startswith("Bearer "):
                    api_key = auth_header[7:]  # Remove "Bearer " prefix
                    if api_key.startswith("rb_sk_"):
                        return RationalBloksClient(api_key)
        except (LookupError, AttributeError):
            pass
        
        return None
    
    def _get_init_options(self) -> InitializationOptions:
        # Get MCP initialization options for STDIO transport
        # Returns server metadata and capability declarations
        # WHY: MCP handshake requires server capabilities advertisement
        
        return InitializationOptions(
            server_name="rationalbloks",
            server_version=__version__,
            capabilities=self.server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
            instructions="RationalBloks MCP Server - Enterprise Backend-as-a-Service for AI agents. Build production APIs from JSON schemas.",
            website_url="https://rationalbloks.com",
        )
    
    def run(self, transport: str = "stdio") -> None:
        # Run the MCP server with the specified transport
        # transport: "stdio" for local IDEs or "http" for cloud deployment
        # Single entry point that routes to STDIO or HTTP transport
        
        if transport == "http":
            self._run_http()
        else:
            self._run_stdio()


# ============================================================================
# STDIO TRANSPORT - Local IDE Integration
# ============================================================================
    
    def _run_stdio(self) -> None:
        # Run in STDIO mode for Cursor, VS Code, Claude Desktop
        # Uses asyncio event loop with stdio_server context manager
        # WHY: IDEs communicate via stdin/stdout pipes
        asyncio.run(self._stdio_async())
    
    async def _stdio_async(self) -> None:
        # Async STDIO handler with MCP stream management
        # Single code path: open streams → run server → close streams
        # WHY: MCP requires bidirectional async stream communication
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self._get_init_options())


# ============================================================================
# HTTP TRANSPORT - Cloud/Smithery Deployment
# ============================================================================
    
    def _run_http(self) -> None:
        # Run in HTTP mode for Smithery and cloud agents using Streamable HTTP
        # Creates Starlette ASGI application with MCP session management
        # WHY: Cloud deployments require HTTP/SSE transport instead of STDIO
        from starlette.applications import Starlette
        from starlette.routing import Route, Mount
        from starlette.responses import JSONResponse
        from starlette.middleware.cors import CORSMiddleware
        from starlette.types import Receive, Scope, Send
        import uvicorn
        
        # Create session manager for Streamable HTTP
        # Handles MCP protocol over HTTP with Server-Sent Events
        session_manager = StreamableHTTPSessionManager(
            app=self.server,
            json_response=True,   # Use JSON responses for compatibility
            stateless=True,       # Stateless for horizontal scalability
        )
        
        async def server_card(request):
            # MCP Server Card for Smithery discovery with comprehensive metadata
            # Provides machine-readable server capabilities and authentication requirements
            # WHY: Smithery marketplace needs structured server metadata for discovery
            
            return JSONResponse({
                "name": "rationalbloks",
                "displayName": "RationalBloks",
                "version": __version__,
                "description": "Enterprise-grade Backend-as-a-Service platform for AI agents. Build production APIs from JSON schemas in minutes.",
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
                    "properties": {
                        "apiKey": {
                            "type": "string",
                            "title": "API Key",
                            "description": "Your RationalBloks API key (get it from https://rationalbloks.com/settings). Optional for browsing documentation.",
                            "default": "",
                            "x-from": {"header": "authorization"}
                        },
                        "baseUrl": {
                            "type": "string",
                            "title": "API Gateway URL",
                            "description": "RationalBloks API Gateway URL",
                            "default": "https://logicblok.rationalbloks.com"
                        },
                        "timeout": {
                            "type": "number",
                            "title": "Timeout",
                            "description": "Request timeout in seconds",
                            "default": 30
                        },
                        "logLevel": {
                            "type": "string",
                            "title": "Log Level",
                            "description": "Logging level: DEBUG, INFO, WARNING, ERROR",
                            "default": "INFO",
                            "enum": ["DEBUG", "INFO", "WARNING", "ERROR"]
                        }
                    }
                }
            })
        
        async def health(request):
            # Health check endpoint for Kubernetes liveness/readiness probes
            # Simple status check with version information
            # WHY: K8s needs health endpoint to manage pod lifecycle
            
            return JSONResponse({"status": "ok", "version": __version__})
        
        async def handle_streamable(scope: Scope, receive: Receive, send: Send):
            # Handle Streamable HTTP requests for MCP protocol
            # Delegates to session manager for MCP JSON-RPC handling
            # WHY: MCP over HTTP uses JSON-RPC 2.0 with SSE for streaming
            
            await session_manager.handle_request(scope, receive, send)
        
        @contextlib.asynccontextmanager
        async def lifespan(app: Starlette) -> AsyncIterator[None]:
            # Application lifespan manager for session manager
            # Ensures proper startup and shutdown of MCP session infrastructure
            # WHY: ASGI lifespan protocol for resource management
            
            async with session_manager.run():
                yield
        
        # Build Starlette ASGI application
        app = Starlette(
            debug=False,
            routes=[
                Route("/.well-known/mcp/server-card.json", endpoint=server_card, methods=["GET"]),
                Route("/health", endpoint=health, methods=["GET"]),
                Mount("/", app=handle_streamable),  # MCP JSON-RPC endpoint at root
            ],
            lifespan=lifespan,
        )
        
        # Add CORS middleware for browser-based clients
        # Allows cross-origin requests from web-based AI agents
        app = CORSMiddleware(
            app,
            allow_origins=["*"],
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["*"],
            expose_headers=["Mcp-Session-Id"],
        )
        
        # Server configuration from environment
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("HOST", "0.0.0.0")
        
        print(f"[rationalbloks-mcp] Streamable HTTP server starting on {host}:{port}", file=sys.stderr)
        print(f"[rationalbloks-mcp] MCP endpoint: http://{host}:{port}/mcp", file=sys.stderr)
        
        uvicorn.run(app, host=host, port=port, log_level="info")
