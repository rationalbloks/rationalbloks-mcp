# ============================================================================
# RATIONALBLOKS MCP - BASE SERVER
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Base MCP server class for the Backend mode.
# Contains shared server initialization and handler registration.
#
# ARCHITECTURE:
# - BaseMCPServer provides common MCP infrastructure
# - BackendMCPServer adds 47 tools and handlers
# ============================================================================

import json
import sys
from contextvars import ContextVar
from typing import Any, Callable

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel.server import NotificationOptions
from mcp.types import (
    Tool,
    ToolAnnotations,
    TextContent,
    Prompt,
    GetPromptResult,
    Resource,
    Icon,
    ListToolsResult,
    CallToolResult,
    ListPromptsResult,
    ListResourcesResult,
    ReadResourceResult,
    TextResourceContents,
)
from starlette.requests import Request

from .auth import validate_api_key, extract_api_key_from_request
from .transport import run_stdio, run_http

# The in-flight HTTP request for the current tool call. SDK 2.0 hands the request to
# handlers via ctx.request (it removed Server.request_context), so on_call_tool stashes
# it here for get_api_key_for_request to read during HTTP per-request auth. A ContextVar
# is task-local, so concurrent requests never read each other's key. None on stdio.
_current_request: ContextVar = ContextVar("rationalbloks_mcp_current_request", default=None)

# Public API
__all__ = [
    "BaseMCPServer",
    "create_mcp_server",
]


# ============================================================================
# STATIC RESOURCE CONTENT
# ============================================================================

DOCS_GETTING_STARTED = """# Getting Started with RationalBloks MCP

## Quick Start

1. Get your API key from https://rationalbloks.com/settings
2. Set environment variable: export RATIONALBLOKS_API_KEY=rb_sk_...
3. Run the server: uvx rationalbloks-mcp

## Tools (47 total)

RationalBloks MCP provides 47 infrastructure tools across 3 categories:

- **Relational** (21 tools): Create, deploy, and manage PostgreSQL REST APIs
- **Graph Schema** (11 tools): Create, deploy, and manage Neo4j Graph APIs
- **Graph Data** (15 tools): CRUD, search, traverse, and bulk operations on graph data

For AI knowledge processing, connect to the Graforest MCP endpoint separately.

## Need Help?

Visit https://rationalbloks.com/docs for full documentation.
"""

DOCS_SCHEMA_REFERENCE = """# RationalBloks Schema Reference

═══════════════════════════════════════════════════════════════════════════
CRITICAL SCHEMA RULES:
═══════════════════════════════════════════════════════════════════════════

## 1. FLAT FORMAT (REQUIRED)

✅ CORRECT:
{
  "users": {
    "email": {"type": "string", "max_length": 255, "required": true, "unique": true},
    "name": {"type": "string", "max_length": 100, "required": true}
  },
  "posts": {
    "title": {"type": "string", "max_length": 200, "required": true},
    "content": {"type": "text"},
    "user_id": {"type": "uuid", "foreign_key": "users.id"}
  }
}

❌ WRONG (DO NOT nest under 'fields'):
{
  "users": {
    "fields": {
      "email": {"type": "string"}
    }
  }
}

## 2. Field Types

- string: MUST have max_length (e.g., "max_length": 255)
- text: Long text fields
- integer: Whole numbers
- decimal: MUST have precision and scale (e.g., "precision": 10, "scale": 2)
- boolean: True/false values
- uuid: Primary/foreign keys
- date: Date only
- datetime: Date and time (NOT "timestamp")
- json: JSON data

## 3. Automatic Fields (DO NOT define)

- id (uuid, primary key)
- created_at (datetime)
- updated_at (datetime)

## 4. User Authentication

❌ NEVER create: users, customers, employees, members tables
✅ USE: built-in app_users table with foreign keys

Example:
{
  "employee_profiles": {
    "user_id": {"type": "uuid", "foreign_key": "app_users.id", "required": true},
    "department": {"type": "string", "max_length": 100}
  }
}

## 5. Authorization

Add user_id → app_users.id for user-owned resources:
{
  "orders": {
    "user_id": {"type": "uuid", "foreign_key": "app_users.id"},
    "total": {"type": "decimal", "precision": 10, "scale": 2}
  }
}

## 6. Field Options

- required: true/false
- unique: true/false
- default: any value
- enum: ["value1", "value2"]
- foreign_key: "table_name.id"

## 7. Backend Engine (Relational Projects)

- python (default): FastAPI backend — mature, full-featured
- rust: Axum backend — faster cold starts, lower memory, high performance

Set via backend_type parameter in create_project.

Full docs: https://infra.rationalbloks.com/documentation
"""

DOCS_API_REFERENCE = """# RationalBloks MCP API Reference

## Relational Tools (21)
- list_projects, get_project, get_schema, get_user_info, list_clusters
- get_job_status, get_project_info, get_version_history
- get_template_schemas, get_subscription_status, get_project_usage
- get_project_storage_usage, list_project_files
- get_schema_at_version, create_project, update_schema
- deploy_staging, deploy_production, delete_project
- rollback_project, rename_project

## Graph Schema Tools (11)
- get_graph_schema, get_graph_template_schemas
- get_graph_version_history, get_graph_schema_at_version
- get_graph_project_info, create_graph_project
- update_graph_schema, deploy_graph_staging, deploy_graph_production
- delete_graph_project, rollback_graph_project

## Graph Data Tools (15)
- create_graph_node, get_graph_node, list_graph_nodes
- update_graph_node, delete_graph_node
- create_graph_relationship, get_node_relationships, delete_graph_relationship
- bulk_create_graph_nodes, bulk_create_graph_relationships
- search_graph_nodes, fulltext_search_graph, traverse_graph
- get_graph_statistics, get_graph_data_schema

For AI knowledge processing tools, connect to the Graforest MCP endpoint.
For full documentation, visit https://rationalbloks.com/docs
"""


def create_mcp_server(
    name: str,
    version: str,
    instructions: str,
    handlers: dict[str, Callable],
) -> Server:
    # Create a configured MCP Server. SDK 2.0 registers request handlers as constructor
    # callbacks (the 1.x decorator API was removed), so `handlers` (built by
    # BaseMCPServer._build_handlers) is expanded into the constructor.
    return Server(
        name=name,
        version=version,
        instructions=instructions,
        website_url="https://rationalbloks.com",
        icons=[
            Icon(src="https://rationalbloks.com/logo.svg", mimeType="image/svg+xml"),
            Icon(src="https://rationalbloks.com/logo.png", mimeType="image/png", sizes=["128x128"]),
        ],
        **handlers,
    )


class BaseMCPServer:
    # Base MCP server with shared infrastructure
    # Provides: Server initialization, common handlers, transport layer, auth
    # Subclasses add: Mode-specific tools and handlers
    
    def __init__(
        self,
        name: str,
        version: str,
        instructions: str,
        api_key: str | None = None,
        http_mode: bool = False,
    ) -> None:
        # Initialize base MCP server
        # CHAIN: Validate API key first, fail immediately if invalid
        self.name = name
        self.version = version
        self.instructions = instructions
        self.http_mode = http_mode

        # Validate API key for STDIO mode
        if not http_mode:
            is_valid, error = validate_api_key(api_key)
            if not is_valid:
                raise ValueError(error)
            self.api_key = api_key
        else:
            self.api_key = None

        # Registries populated by subclasses via register_*(). Initialized BEFORE the
        # Server is built so the handler closures can read them lazily at call time — a
        # subclass registers its tools/prompts after super().__init__() returns.
        self._tools: list[dict] = []
        self._tool_handlers: dict[str, Callable] = {}
        self._prompts: list[Prompt] = []
        self._prompt_handlers: dict[str, Callable] = {}
        self._static_resources: dict[str, str] = {
            "rationalbloks://docs/getting-started": DOCS_GETTING_STARTED,
            "rationalbloks://docs/schema-reference": DOCS_SCHEMA_REFERENCE,
            "rationalbloks://docs/api-reference": DOCS_API_REFERENCE,
        }

        # SDK 2.0 takes request handlers as constructor callbacks, so build them first
        # and pass them in. Nothing to register after construction.
        self.server = create_mcp_server(name, version, instructions, self._build_handlers())
    
    def register_tools(self, tools: list[dict]) -> None:
        # Register tools for this server mode
        self._tools.extend(tools)
    
    def register_tool_handler(self, name: str, handler: Callable) -> None:
        # Register a handler function for a tool
        self._tool_handlers[name] = handler
    
    def register_prompts(self, prompts: list[Prompt]) -> None:
        # Register prompts for this server mode
        self._prompts.extend(prompts)
    
    def register_prompt_handler(self, name: str, handler: Callable) -> None:
        # Register a handler function for a prompt
        self._prompt_handlers[name] = handler
    
    def _build_handlers(self) -> dict[str, Callable]:
        # Build the MCP request handlers as closures over self. SDK 2.0 takes them as
        # Server constructor callbacks (the 1.x decorator API was removed); each gets
        # (ctx, params) and returns a typed *Result. The closures read the registries
        # at CALL time, so tools/prompts a subclass registers after super().__init__()
        # are still served.

        async def on_list_tools(ctx, params) -> ListToolsResult:
            tools_list = []
            for tool in self._tools:
                annotations = None
                if "annotations" in tool:
                    ann = tool["annotations"]
                    annotations = ToolAnnotations(
                        readOnlyHint=ann.get("readOnlyHint"),
                        destructiveHint=ann.get("destructiveHint"),
                        idempotentHint=ann.get("idempotentHint"),
                        openWorldHint=ann.get("openWorldHint"),
                    )
                tools_list.append(Tool(
                    name=tool["name"],
                    title=tool.get("title"),
                    description=tool["description"],
                    inputSchema=tool["inputSchema"],
                    annotations=annotations,
                ))
            return ListToolsResult(tools=tools_list)

        async def on_call_tool(ctx, params) -> CallToolResult:
            # SDK 2.0 removed Server.request_context; the HTTP request now arrives on
            # ctx.request. Stash it so get_api_key_for_request can read the bearer key
            # for this call (HTTP mode). None on stdio, where the stored key is used.
            _current_request.set(getattr(ctx, "request", None))

            name = params.name
            arguments = params.arguments or {}
            valid_tools = [t["name"] for t in self._tools]
            if name not in valid_tools:
                raise ValueError(f"Unknown tool: {name}")

            # Specific handler first, then the wildcard handler.
            handler = self._tool_handlers.get(name) or self._tool_handlers.get("*")
            if not handler:
                raise ValueError(f"No handler registered for tool: {name}")

            # NO outer try/except. Chain-of-events: let exceptions propagate so the SDK
            # marks the result isError=True. Silently returning "Error: ..." text lets
            # an agent chain a next step after a failed tool call.
            result = await handler(name, arguments)
            formatted = json.dumps(result, indent=2, default=str)
            return CallToolResult(content=[TextContent(type="text", text=formatted)])

        async def on_list_prompts(ctx, params) -> ListPromptsResult:
            return ListPromptsResult(prompts=self._prompts)

        async def on_get_prompt(ctx, params) -> GetPromptResult:
            handler = self._prompt_handlers.get(params.name)
            if not handler:
                raise ValueError(f"Unknown prompt: {params.name}")
            return handler(params.name, params.arguments)

        async def on_list_resources(ctx, params) -> ListResourcesResult:
            resources = []
            for uri, _ in self._static_resources.items():
                name = uri.split("/")[-1].replace("-", " ").title()
                resources.append(Resource(
                    uri=uri,
                    name=f"{name} Guide",
                    description=f"Documentation: {name}",
                    mimeType="text/markdown",
                ))
            return ListResourcesResult(resources=resources)

        async def on_read_resource(ctx, params) -> ReadResourceResult:
            uri_str = str(params.uri)
            if uri_str not in self._static_resources:
                raise ValueError(f"Unknown resource: {uri_str}")
            return ReadResourceResult(contents=[
                TextResourceContents(
                    uri=params.uri,
                    text=self._static_resources[uri_str],
                    mimeType="text/markdown",
                ),
            ])

        return {
            "on_list_tools": on_list_tools,
            "on_call_tool": on_call_tool,
            "on_list_prompts": on_list_prompts,
            "on_get_prompt": on_get_prompt,
            "on_list_resources": on_list_resources,
            "on_read_resource": on_read_resource,
        }
    
    def get_api_key_for_request(self) -> str | None:
        # Get the API key for the current request.
        # STDIO mode: the key validated at startup.
        # HTTP mode: the bearer key from the in-flight request, stashed by on_call_tool
        # (SDK 2.0 hands the request to handlers via ctx.request, not a server context).
        if not self.http_mode:
            return self.api_key

        request = _current_request.get()
        if request is None or not isinstance(request, Request):
            return None
        return extract_api_key_from_request(request)
    
    def get_init_options(self) -> InitializationOptions:
        # Get MCP initialization options
        return InitializationOptions(
            server_name=self.name,
            server_version=self.version,
            capabilities=self.server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={},
            ),
            instructions=self.instructions,
            website_url="https://rationalbloks.com",
        )
    
    def run(self, transport: str = "stdio") -> None:
        # Run the MCP server with specified transport
        # transport: "stdio" for local IDEs or "http" for cloud
        if transport == "http":
            run_http(
                server=self.server,
                name=self.name,
                version=self.version,
                description=self.instructions,
                init_options=self.get_init_options(),
            )
        else:
            run_stdio(
                server=self.server,
                init_options=self.get_init_options(),
            )
