# ============================================================================
# RATIONALBLOKS MCP - THE SERVER
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# One server: its instructions, prompts and resources, and the tools LogicBlok's MCP gateway defines. The
# tools are the gateway's rows (logicblok/mcp_gateway.py, THE TOOLS), listed from GET /api/mcp/tools on every
# tools/list with the request's key, or without one, and called through POST /api/mcp/execute. A list or a
# call the gateway refuses fails with its reason. The package keeps no copy of a tool, so a tool changes with
# one LogicBlok deploy and every client lists it at its next tools/list.
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
    CallToolResult,
    GetPromptResult,
    Icon,
    ListPromptsResult,
    ListResourcesResult,
    ListToolsResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    ReadResourceResult,
    Resource,
    TextContent,
    TextResourceContents,
    Tool,
    ToolAnnotations,
)
from starlette.requests import Request

from .._version import __version__
from ..core.auth import extract_api_key_from_request, stdio_api_key
from ..core.transport import run_http, run_stdio
from .client import LogicBlokClient

# Public API
__all__ = [
    "BackendMCPServer",
    "create_backend_server",
]

# The in-flight HTTP request for the current tool call or tool list. SDK 2.0 hands the request
# to handlers via ctx.request (it removed Server.request_context), so on_call_tool and
# on_list_tools stash it here for get_api_key_for_request to read during HTTP per-request auth.
# A ContextVar is task-local, so concurrent requests never read each other's key. None on stdio.
_current_request: ContextVar = ContextVar("rationalbloks_mcp_current_request", default=None)


# ============================================================================
# RESOURCES
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
- row_version (integer: the row's version, 1 on insert and one more on every update)

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
stated count, writes that state the row_version they read): the get_schema_reference tool.

## 7. Backend Engine (Relational Projects)

- python (default): FastAPI backend — mature, full-featured
- rust: Axum backend — faster cold starts, lower memory, high performance

Set via backend_type parameter in create_project.

Full docs: https://rationalbloks.com/documentation
"""

API_REFERENCE_URI = "rationalbloks://docs/api-reference"


def api_reference(catalog: list) -> str:
    # The rationalbloks://docs/api-reference resource, written from the catalog the gateway serves, so it
    # names exactly the tools a client lists, each in its group under the kind its annotations declare:
    # Read, Write (never loses data) or Destructive
    def kind(tool: dict) -> str:
        hints = tool["annotations"]
        if hints["readOnlyHint"]:
            return "Read"
        return "Destructive" if hints["destructiveHint"] else "Write"

    lines = ["# RationalBloks MCP API Reference", "",
             "Read tools only read. Write tools never lose data. Destructive tools can, and declare destructiveHint."]
    for group in dict.fromkeys(tool["group"] for tool in catalog):
        lines += ["", f"## {group}"]
        for name in ("Read", "Write", "Destructive"):
            names = [tool["name"] for tool in catalog if tool["group"] == group and kind(tool) == name]
            if names:
                lines.append(f"- {name}: {', '.join(names)}")
    lines += ["", "For full documentation, visit https://rationalbloks.com/documentation"]
    return "\n".join(lines) + "\n"


# ============================================================================
# PROMPTS
# ============================================================================

BACKEND_PROMPTS = [
    Prompt(
        name="create-project-from-description",
        title="Create Project from Description",
        description="Generate a complete RationalBloks project schema from a plain English description",
        arguments=[
            PromptArgument(
                name="description",
                description="Plain English description of the data model you want to create",
                required=True,
            )
        ],
    ),
    Prompt(
        name="fix-schema-errors",
        title="Fix Schema Errors",
        description="Analyze and fix common schema format errors",
        arguments=[
            PromptArgument(
                name="schema",
                description="The JSON schema that is causing errors",
                required=True,
            ),
            PromptArgument(
                name="error_message",
                description="The error message you received",
                required=False,
            ),
        ],
    ),
]

GRAPH_PROMPTS = [
    Prompt(
        name="create-graph-project-from-description",
        title="Create Graph Project from Description",
        description="Generate a complete RationalBloks graph project schema from a plain English description",
        arguments=[
            PromptArgument(
                name="description",
                description="Plain English description of the graph data model you want to create",
                required=True,
            )
        ],
    ),
    Prompt(
        name="populate-graph-from-text",
        title="Populate a Graph from Text",
        description="Fill a deployed graph project with the entities and relationships a text states, without duplicates",
        arguments=[
            PromptArgument(name="project_id", description="The graph project's ID", required=True),
            PromptArgument(name="text", description="The text to read", required=True),
            PromptArgument(name="environment", description="staging (default) or production", required=False),
        ],
    ),
    Prompt(
        name="explore-graph",
        title="Explore a Graph",
        description="Explore a deployed graph project, about a topic or as a whole, and summarise what it holds",
        arguments=[
            PromptArgument(name="project_id", description="The graph project's ID", required=True),
            PromptArgument(name="topic", description="What to explore (optional: the whole graph)", required=False),
            PromptArgument(name="environment", description="staging (default) or production", required=False),
        ],
    ),
]


# ============================================================================
# THE SERVER
# ============================================================================

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


class BackendMCPServer:
    # The MCP server: the instructions, the prompts and the resources it holds, and the tools of LogicBlok's
    # gateway, listed on every tools/list and called through it

    INSTRUCTIONS = """RationalBloks: production REST APIs (PostgreSQL) and graph APIs (Neo4j) generated from JSON schemas and deployed onto your own resource pools.

CHANGE A SCHEMA SAFELY
1. get_schema (tables/fields for a slice; its version pins the save)
2. preview_schema_change: the diff and the deploy plan, nothing saved
3. patch_schema (add, rename, set; never drops), drop_schema_items (drops) or update_schema (the whole schema)
4. deploy_staging, then get_job_status until completed or failed
A deploy tool refuses a plan that drops data and names the drops; deploy_destructive applies it once the drops are confirmed intended. deploy_production promotes staging.

REBUILD WITHOUT A SCHEMA CHANGE: redeploy_project (staging); deploy_production when staging runs what production runs.

MODULES (your frontends and backends, built from GitHub): list_modules, deploy_module, redeploy_module, set_module_env (values are write-only), freeze_module, unfreeze_module, scale_module, set_module_resources, update_module, delete_module.

JOBS: deploys, promotions, rollbacks and module builds are jobs; list_project_jobs finds a lost job_id. A failed job's failure_side says whether the project's input caused it.

DELETE: delete_project/delete_graph_project need confirm_name (the project's name) and only schedule it; restore_project cancels.

START: list_projects; create_project needs a cluster_id from list_clusters; get_template_schemas shows valid schemas, get_schema_reference the advanced features (__policy__, computed columns, __constraints__, deletes with a stated count, writes that state the row_version they read).

RELATIONAL: FLAT {"table": {"field": {"type": ...}}}; a string has max_length; "datetime", not "timestamp"; never define id, created_at, updated_at, row_version; users are the built-in app_users (foreign_key "app_users.id").
GRAPH: {"nodes": {...}, "relationships": {...}}; PascalCase entities, UPPER_SNAKE_CASE relationships.

Setup and Claude Code permissions: https://rationalbloks.com/documentation"""

    def __init__(
        self,
        api_key: str | None = None,
        http_mode: bool = False,
    ) -> None:
        # STDIO mode carries one key, its shape checked here at startup; HTTP mode reads a key per request
        self.name = "rationalbloks-backend"
        self.version = __version__
        self.http_mode = http_mode
        self.api_key = None if http_mode else stdio_api_key(api_key)
        self._static_resources = {
            "rationalbloks://docs/getting-started": DOCS_GETTING_STARTED,
            "rationalbloks://docs/schema-reference": DOCS_SCHEMA_REFERENCE,
        }
        self._prompts = BACKEND_PROMPTS + GRAPH_PROMPTS
        self._prompt_handlers = {
            "create-project-from-description": self._handle_create_project_prompt,
            "fix-schema-errors": self._handle_fix_schema_prompt,
            "create-graph-project-from-description": self._handle_create_graph_project_prompt,
            "populate-graph-from-text": self._handle_populate_graph_prompt,
            "explore-graph": self._handle_explore_graph_prompt,
        }
        # SDK 2.0 takes request handlers as constructor callbacks, so they are built first and passed in
        self.server = create_mcp_server(self.name, self.version, self.INSTRUCTIONS, self._build_handlers())

    async def _catalog(self) -> list:
        # The tools as the gateway serves them (GET /api/mcp/tools): with the request's key, the tools it may
        # call, so a read-only key's server lists the read tools alone and a client allows all of it with one
        # rule; without a key, every tool (a directory reading the server, which can call none of them)
        async with LogicBlokClient(self.get_api_key_for_request()) as client:
            return await client.list_tools()

    def _keyed_client(self) -> LogicBlokClient:
        # A LogicBlok client for the request's API key, which a tool call needs
        api_key = self.get_api_key_for_request()
        if not api_key:
            raise ValueError("No RationalBloks API key: set RATIONALBLOKS_API_KEY (a local server) or send the header "
                             "Authorization: Bearer rb_sk_... (the hosted server). Create one at "
                             "https://rationalbloks.com/settings")
        return LogicBlokClient(api_key)

    def _build_handlers(self) -> dict:
        # The MCP request handlers, as closures over self (SDK 2.0 takes them as Server constructor callbacks;
        # each gets (ctx, params) and returns a typed *Result)

        async def on_list_tools(ctx, params) -> ListToolsResult:
            # The gateway's catalog, fetched for this request. A failed fetch (a refused key, RationalBloks
            # unreachable) is raised as the protocol's internal error (-32603) with its message; a plain
            # exception would reach the client as code 0, which is no JSON-RPC error code.
            _current_request.set(getattr(ctx, "request", None))
            try:
                catalog = await self._catalog()
            except Exception as error:
                raise MCPError(INTERNAL_ERROR, str(error)) from error
            return ListToolsResult(tools=[
                Tool(
                    name=tool["name"],
                    title=tool["title"],
                    description=tool["description"],
                    inputSchema=tool["inputSchema"],
                    annotations=ToolAnnotations(**tool["annotations"]),
                )
                for tool in catalog
            ])

        async def on_call_tool(ctx, params) -> CallToolResult:
            # Every tool passes through to the gateway (POST /api/mcp/execute), which refuses a tool it does not
            # define and a call that does not fit the tool. The call's one try: a failed call is a result
            # marked is_error that carries the failure (a missing argument, a busy project naming its job, a
            # plan that drops data), so the agent reads why and never chains a next step on it. SDK 2.0
            # answers an exception raised here with a bare "Internal server error" instead.
            _current_request.set(getattr(ctx, "request", None))
            try:
                async with self._keyed_client() as client:
                    result = await client.execute(params.name, params.arguments or {})
            except Exception as error:
                return CallToolResult(content=[TextContent(type="text", text=str(error))], is_error=True)
            return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2, default=str))])

        async def on_list_prompts(ctx, params) -> ListPromptsResult:
            return ListPromptsResult(prompts=self._prompts)

        async def on_get_prompt(ctx, params) -> GetPromptResult:
            handler = self._prompt_handlers.get(params.name)
            if not handler:
                raise ValueError(f"Unknown prompt: {params.name}")
            return handler(params.name, params.arguments)

        async def on_list_resources(ctx, params) -> ListResourcesResult:
            resources = []
            for uri in [*self._static_resources, API_REFERENCE_URI]:
                name = uri.split("/")[-1].replace("-", " ").title()
                resources.append(Resource(
                    uri=uri,
                    name=f"{name} Guide",
                    description=f"Documentation: {name}",
                    mimeType="text/markdown",
                ))
            return ListResourcesResult(resources=resources)

        async def on_read_resource(ctx, params) -> ReadResourceResult:
            # The API reference is written from the catalog the gateway serves this request
            uri_str = str(params.uri)
            _current_request.set(getattr(ctx, "request", None))
            if uri_str == API_REFERENCE_URI:
                text = api_reference(await self._catalog())
            elif uri_str in self._static_resources:
                text = self._static_resources[uri_str]
            else:
                raise ValueError(f"Unknown resource: {uri_str}")
            return ReadResourceResult(contents=[TextResourceContents(uri=params.uri, text=text, mimeType="text/markdown")])

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
            instructions=self.INSTRUCTIONS,
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
                description=self.INSTRUCTIONS,
            )
        else:
            run_stdio(
                server=self.server,
                init_options=self.get_init_options(),
            )

    def _handle_create_project_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        # Handle create-project-from-description prompt
        description = arguments.get("description", "") if arguments else ""

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Create a RationalBloks project schema for: {description}

═══════════════════════════════════════════════════════════════════════════
CRITICAL SCHEMA RULES - FOLLOW EXACTLY:
═══════════════════════════════════════════════════════════════════════════

1. FLAT FORMAT (REQUIRED):
   ✅ CORRECT: {{"users": {{"email": {{"type": "string", "max_length": 255}}}}}}
   ❌ WRONG: {{"users": {{"fields": {{"email": {{"type": "string"}}}}}}}}
   DO NOT nest under 'fields' key!

2. FIELD TYPE REQUIREMENTS:
   • string: MUST have "max_length" (e.g., "max_length": 255)
   • decimal: MUST have "precision" and "scale" (e.g., "precision": 10, "scale": 2)
   • datetime: Use "datetime" NOT "timestamp"
   • ALL fields: MUST have "type" property

3. AUTOMATIC FIELDS (DON'T define):
   • id (uuid, primary key)
   • created_at (datetime)
   • updated_at (datetime)
   • row_version (integer: the row's version, 1 on insert and one more on every update)

4. USER AUTHENTICATION:
   ❌ NEVER create "users", "customers", "employees", "members" tables
   ✅ USE built-in app_users table

   Example:
   {{
     "employee_profiles": {{
       "user_id": {{"type": "uuid", "foreign_key": "app_users.id", "required": true}},
       "department": {{"type": "string", "max_length": 100}}
     }}
   }}

5. AUTHORIZATION (user ownership):
   • Add user_id foreign key to app_users.id for user-owned resources

   Example:
   {{
     "orders": {{
       "user_id": {{"type": "uuid", "foreign_key": "app_users.id"}},
       "total": {{"type": "decimal", "precision": 10, "scale": 2}}
     }}
   }}

6. FIELD OPTIONS:
   • required: true/false
   • unique: true/false
   • default: any value
   • enum: ["value1", "value2"]
   • foreign_key: "table_name.id"

AVAILABLE TYPES: string, text, integer, decimal, boolean, uuid, date, datetime, json, uuid_array, integer_array, text_array, float_array

   Array types store PostgreSQL native arrays with automatic GIN indexing:
   • uuid_array: UUID[] — for sets of references (e.g., tensor coordinates)
   • integer_array: BIGINT[] — for dimension indices, integer sets
   • text_array: TEXT[] — for tags, categories, label sets
   • float_array: DOUBLE PRECISION[] — for weight vectors, scores

═══════════════════════════════════════════════════════════════════════════

Generate the schema now following ALL rules above:""",
                    ),
                )
            ]
        )

    def _handle_fix_schema_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        # Handle fix-schema-errors prompt
        schema = arguments.get("schema", "{}") if arguments else "{}"
        error = arguments.get("error_message", "Unknown error") if arguments else "Unknown error"

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Fix this RationalBloks schema:

Schema:
{schema}

Error: {error}

═══════════════════════════════════════════════════════════════════════════
COMMON SCHEMA ERRORS:
═══════════════════════════════════════════════════════════════════════════

1. NESTED 'fields' KEY:
   ❌ {{"users": {{"fields": {{"email": {{...}}}}}}}}
   ✅ {{"users": {{"email": {{...}}}}}}

2. MISSING TYPE PROPERTY:
   ❌ {{"name": {{"required": true}}}}
   ✅ {{"name": {{"type": "string", "max_length": 100, "required": true}}}}

3. STRING WITHOUT max_length:
   ❌ {{"email": {{"type": "string"}}}}
   ✅ {{"email": {{"type": "string", "max_length": 255}}}}

4. DECIMAL WITHOUT precision/scale:
   ❌ {{"price": {{"type": "decimal"}}}}
   ✅ {{"price": {{"type": "decimal", "precision": 10, "scale": 2}}}}

5. USING "timestamp" INSTEAD OF "datetime":
   ❌ {{"created": {{"type": "timestamp"}}}}
   ✅ {{"created": {{"type": "datetime"}}}}

6. DEFINING AUTOMATIC FIELDS:
   ❌ {{"id": {{...}}}}, {{"created_at": {{...}}}}, {{"updated_at": {{...}}}}, {{"row_version": {{...}}}}
   ✅ Don't define these - they're automatic. A column of your own named row_version is renamed with patch_schema rename_field

7. CREATING users/customers/employees TABLE:
   ❌ {{"users": {{"email": {{...}}, "password": {{...}}}}}}
   ✅ Use app_users pattern with foreign key

CHECK ALL THESE ISSUES and provide the corrected schema:""",
                    ),
                )
            ]
        )

    def _handle_create_graph_project_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        # Handle create-graph-project-from-description prompt
        description = arguments.get("description", "") if arguments else ""

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Create a RationalBloks graph project schema for: {description}

═══════════════════════════════════════════════════════════════════════════
GRAPH SCHEMA FORMAT — FOLLOW EXACTLY:
═══════════════════════════════════════════════════════════════════════════

Graph schemas define nodes (entities) and relationships — NOT flat database tables.
Each field is a dict with "type" and optional "required": true (defaults to false).

STRUCTURE:
{{
  "nodes": {{
    "EntityName": {{
      "description": "What this entity represents",
      "flat_labels": ["AdditionalLabel"],
      "schema": {{
        "field_name": {{"type": "string", "required": true}},
        "other_field": {{"type": "integer"}}
      }}
    }}
  }},
  "relationships": {{
    "RELATIONSHIP_TYPE": {{
      "from": "EntityName",
      "to": "OtherEntity",
      "cardinality": "MANY_TO_MANY",
      "data_schema": {{
        "field_name": {{"type": "date"}}
      }}
    }}
  }}
}}

FIELD TYPES: string, integer, float, boolean, date, json

CARDINALITY: ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY

RULES:
1. "nodes" key is REQUIRED — must contain at least one entity
2. Each entity needs "description" and "schema" with field definitions
3. Each field is {{"type": "...", "required": true/false}} — required defaults to false
4. Relationship "from"/"to" name an entity: its path ("Vehicle:Car"), or its name ("Car") when no other entity has it
5. Relationship types: UPPER_SNAKE_CASE (e.g., FOLLOWS, CREATED_BY)
6. Entity names: PascalCase (e.g., Person, Product)
7. Nest entities inside parents to create type hierarchies: a child inherits its parent's labels and
   fields (no need to restate one), and a relationship end naming the parent accepts the child too
8. Automatic fields (id, created_at, updated_at) are NOT needed

HIERARCHICAL EXAMPLE:
{{
  "nodes": {{
    "Vehicle": {{
      "description": "A vehicle",
      "flat_labels": ["Transport"],
      "schema": {{
        "make": {{"type": "string", "required": true}},
        "model": {{"type": "string", "required": true}},
        "year": {{"type": "integer"}}
      }},
      "Car": {{
        "description": "A car (inherits Vehicle's labels and its make, model and year)",
        "flat_labels": ["Automobile"],
        "schema": {{
          "doors": {{"type": "integer", "required": true}},
          "electric": {{"type": "boolean"}}
        }}
      }}
    }}
  }}
}}

Generate the graph schema now following ALL rules above:""",
                    ),
                )
            ]
        )

    def _handle_populate_graph_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        # populate-graph-from-text: graforest's ingest prompt with its rules rewritten (graforest roadmap 2.5),
        # so a second pass over the same text adds nothing twice
        arguments = arguments or {}
        project_id = arguments.get("project_id", "")
        environment = arguments.get("environment") or "staging"
        text = arguments.get("text", "")

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Fill the RationalBloks graph project {project_id} ({environment}) with what the text below states.

1. Call get_graph_data_schema (project_id {project_id}, environment {environment}). It gives every entity's
   fields, a nested entity's inherited ones included (each names the entity that declares it), and every
   relationship's ends (from_types / to_types: the entities each end accepts).
2. List the entities and relationships the text states, each under an entity key or a relationship key
   exactly as the schema gives it. Record only what the text states.
3. Before creating an entity, search for it (fulltext_search_graph with its name) and reuse its entity_id
   when it exists. Give a new one a meaningful entity_id (e.g. "python", "alan-turing").
4. Fill every required field, the inherited ones included. When the schema has source or page fields,
   fill them.
5. Write the new nodes with bulk_create_graph_nodes (one call per entity), then the relationships with
   bulk_create_graph_relationships (one call per relationship). An end whose node is of an entity nested
   under the relationship's own names its entity key in from_type / to_type.
6. Finish with get_graph_statistics, and say what you added and what you found already there.

TEXT:
{text}""",
                    ),
                )
            ]
        )

    def _handle_explore_graph_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        # explore-graph: graforest's explore prompt, on the subgraph read (nodes with their relationships)
        arguments = arguments or {}
        project_id = arguments.get("project_id", "")
        environment = arguments.get("environment") or "staging"
        topic = arguments.get("topic", "")
        start = (f"fulltext_search_graph for \"{topic}\", then get_graph_subgraph from the matches as seeds (depth 1)"
                 if topic else "get_graph_subgraph without seeds, for a sample of the graph")

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Explore the RationalBloks graph project {project_id} ({environment}){f' about "{topic}"' if topic else ''}.

1. get_graph_data_schema: the entities, their fields and the relationships that connect them.
2. get_graph_statistics: how many nodes and relationships of each type the graph holds.
3. {start}.
4. Follow what stands out with get_graph_subgraph from those nodes; truncated in its answer means there is more.
5. Summarise what the graph holds: its main entities, how they connect and what stands out, naming each
   node by its name or title.""",
                    ),
                )
            ]
        )


def create_backend_server(
    api_key: str | None = None,
    http_mode: bool = False,
) -> BackendMCPServer:
    # Factory function to create a backend MCP server
    # Returns: Configured BackendMCPServer instance
    return BackendMCPServer(api_key=api_key, http_mode=http_mode)
