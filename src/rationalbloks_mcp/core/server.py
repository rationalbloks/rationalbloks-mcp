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
# - BackendMCPServer adds the tools, their handler, the prompts and the tool list's narrowing
# ============================================================================

import json
from contextvars import ContextVar
from typing import Callable

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel.server import NotificationOptions
from mcp.shared.exceptions import MCPError
from mcp.types import (
    INTERNAL_ERROR,
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

from .auth import stdio_api_key, extract_api_key_from_request
from .transport import run_stdio, run_http

# The in-flight HTTP request for the current tool call or tool list. SDK 2.0 hands the request
# to handlers via ctx.request (it removed Server.request_context), so on_call_tool and
# on_list_tools stash it here for get_api_key_for_request to read during HTTP per-request auth.
# A ContextVar is task-local, so concurrent requests never read each other's key. None on stdio.
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

## Connect

1. Create an API key at https://rationalbloks.com/settings. A read-only key's server lists the
   read tools alone.
2. The hosted server: https://mcp.rationalbloks.com/mcp, with the header
   Authorization: Bearer rb_sk_...
   Or a local one: RATIONALBLOKS_API_KEY=rb_sk_... uvx rationalbloks-mcp@latest

## The Tools

- **Relational projects**: create, read and change PostgreSQL schemas, deploy, promote, roll back
- **Graph projects**: the same for Neo4j schemas, and their data (nodes, relationships, search, traversal)
- **Modules**: your frontends and backends built from GitHub (deploy, redeploy, environment, freeze, scale)

Every tool that can lose data is a tool of its own and declares destructiveHint; the API
reference resource lists them. A deploy tool refuses a plan that drops data and names what it
drops. In Claude Code, allow the server and ask before those:
https://rationalbloks.com/documentation (IDE Setup).

## What Every Relational Project Gets

- PostgreSQL database, migrated automatically on every deploy
- Full CRUD REST endpoints for every table in the schema
- JWT auth: POST /api/auth/register, POST /api/auth/login, refresh-token rotation
- Interactive OpenAPI docs at /docs
- Two environments: staging and production
- Authorization resolved per table: a declared __policy__ wins; else a user FK to
  app_users makes rows owner-scoped (admins see all); else the table is tenant-shared
  reference data readable by any authenticated user of that project

## Deploying

create_project requires a cluster_id — call list_clusters and pass a pool id. It returns
a job_id, not a URL. Poll get_job_status, then call get_project_info, which returns the
live base URL as staging.url and production.url. A job's record is kept: list_project_jobs
reads a project's jobs newest first, with each one's outcome, when a job_id was lost.

## Need Help?

Visit https://rationalbloks.com/documentation for full documentation.
"""

DOCS_SCHEMA_REFERENCE = """# RationalBloks Schema Reference

═══════════════════════════════════════════════════════════════════════════
CRITICAL SCHEMA RULES:
═══════════════════════════════════════════════════════════════════════════

## 1. FLAT FORMAT (REQUIRED)

✅ CORRECT:
{
  "projects": {
    "name": {"type": "string", "max_length": 100, "required": true, "unique": true},
    "description": {"type": "text"}
  },
  "tasks": {
    "title": {"type": "string", "max_length": 200, "required": true},
    "project_id": {"type": "uuid", "foreign_key": "projects.id"}
  }
}

❌ WRONG (DO NOT nest under 'fields'):
{
  "projects": {
    "fields": {
      "name": {"type": "string"}
    }
  }
}

## 2. Field Types

- string: max_length, default 255 (e.g., "max_length": 100)
- text: Long text fields
- integer: Whole numbers
- decimal: precision and scale, default 10 and 2 (e.g., "precision": 12, "scale": 4)
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
- on_delete (beside foreign_key): cascade (default), set_null (needs "nullable": true), restrict, no_action

Advanced features (row policies, computed columns, unique groups, audit trails, deletes with a
stated count): the get_schema_reference tool.

## 7. Backend Engine (Relational Projects)

- python (default): FastAPI backend — mature, full-featured
- rust: Axum backend — faster cold starts, lower memory, high performance

Set via backend_type parameter in create_project.

Full docs: https://rationalbloks.com/documentation
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
        # Both assets are served from the portal's public/ directory; logo.svg and
        # logo.png never existed there and 404'd in every client that fetched them.
        icons=[
            Icon(src="https://rationalbloks.com/favicon.svg", mimeType="image/svg+xml"),
            Icon(src="https://rationalbloks.com/rationalbloks_logo.png", mimeType="image/png", sizes=["1200x250"]),
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

        # STDIO mode carries one key, its shape checked here at startup; HTTP mode reads a key per request
        self.api_key = None if http_mode else stdio_api_key(api_key)

        # Registries populated by subclasses via register_*(). Initialized BEFORE the
        # Server is built so the handler closures can read them lazily at call time — a
        # subclass registers its tools/prompts after super().__init__() returns.
        self._tools: list[dict] = []
        self._tool_handlers: dict[str, Callable] = {}
        self._tool_filter: Callable | None = None
        self._prompts: list[Prompt] = []
        self._prompt_handlers: dict[str, Callable] = {}
        self._static_resources: dict[str, str] = {
            "rationalbloks://docs/getting-started": DOCS_GETTING_STARTED,
            "rationalbloks://docs/schema-reference": DOCS_SCHEMA_REFERENCE,
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

    def register_tool_filter(self, tool_filter: Callable) -> None:
        # Register the narrowing of tools/list: an async callable answering the names of the tools the
        # request may call, or None to offer every registered tool
        self._tool_filter = tool_filter

    def register_prompts(self, prompts: list[Prompt]) -> None:
        # Register prompts for this server mode
        self._prompts.extend(prompts)

    def register_prompt_handler(self, name: str, handler: Callable) -> None:
        # Register a handler function for a prompt
        self._prompt_handlers[name] = handler

    def register_resource(self, uri: str, text: str) -> None:
        # Register a markdown resource a subclass writes (the API reference, from its tools)
        self._static_resources[uri] = text

    def _build_handlers(self) -> dict[str, Callable]:
        # Build the MCP request handlers as closures over self. SDK 2.0 takes them as
        # Server constructor callbacks (the 1.x decorator API was removed); each gets
        # (ctx, params) and returns a typed *Result. The closures read the registries
        # at CALL time, so tools/prompts a subclass registers after super().__init__()
        # are still served.

        async def on_list_tools(ctx, params) -> ListToolsResult:
            # The registered tools the request may call, as the registered filter answers them. A failed
            # answer (a refused key, RationalBloks unreachable) is raised as the protocol's internal error
            # (-32603) with its message; a plain exception would reach the client as code 0, which is no
            # JSON-RPC error code, with a traceback in the server's log.
            _current_request.set(getattr(ctx, "request", None))
            try:
                allowed = await self._tool_filter() if self._tool_filter else None
            except Exception as error:
                raise MCPError(INTERNAL_ERROR, str(error)) from error
            tools_list = []
            for tool in self._tools:
                if allowed is not None and tool["name"] not in allowed:
                    continue
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

            # The tool call's one try: a failed call is a result marked is_error that carries the
            # failure (a missing argument, a busy project naming its job, a plan that drops data), so
            # the agent reads why and never chains a next step on it. SDK 2.0 answers an exception
            # raised here with a bare "Internal server error" instead.
            try:
                result = await handler(name, arguments)
            except Exception as error:
                return CallToolResult(content=[TextContent(type="text", text=str(error))], is_error=True)
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
            )
        else:
            run_stdio(
                server=self.server,
                init_options=self.get_init_options(),
            )
