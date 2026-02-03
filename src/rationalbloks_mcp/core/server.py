# ============================================================================
# RATIONALBLOKS MCP - BASE SERVER
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Base MCP server class that Backend and Frontend modes extend.
# Contains shared server initialization and handler registration.
#
# ARCHITECTURE:
# - BaseMCPServer provides common MCP infrastructure
# - Backend/Frontend modes add their specific tools and handlers
# - No duplication of server setup logic
# ============================================================================

import json
import os
import sys
from typing import Any, Callable

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel.server import NotificationOptions
from mcp.types import (
    Tool,
    ToolAnnotations,
    TextContent,
    Prompt,
    PromptArgument,
    PromptMessage,
    GetPromptResult,
    Resource,
    Icon,
)
from starlette.requests import Request

from .auth import validate_api_key, extract_api_key_from_request, APIKeyCache
from .transport import run_stdio, run_http

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

## Modes

RationalBloks MCP supports three modes:

- **backend**: API/database tools only (18 tools)
- **frontend**: Frontend generation tools only (5 tools)
- **full**: All tools combined (23 tools) - DEFAULT

Set mode via environment: RATIONALBLOKS_MODE=backend|frontend|full

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

Full docs: https://infra.rationalbloks.com/documentation
"""

DOCS_API_REFERENCE = """# RationalBloks MCP API Reference

## Backend Tools (18)
- list_projects, get_project, get_schema, get_user_info
- get_job_status, get_project_info, get_version_history
- get_template_schemas, get_subscription_status, get_project_usage
- get_schema_at_version, create_project, update_schema
- deploy_staging, deploy_production, delete_project
- rollback_project, rename_project

## Frontend Tools (5)
- clone_template: Clone rationalbloksfront template
- get_template_structure: Explore template structure
- read_template_file: Read file from template
- create_backend: Call Backend MCP to create API
- configure_api_url: Set API URL in frontend .env

For full documentation, visit https://rationalbloks.com/docs
"""


def create_mcp_server(
    name: str,
    version: str,
    instructions: str,
) -> Server:
    """Create a configured MCP Server instance.
    
    Args:
        name: Server name (e.g., "rationalbloks", "rationalbloks-frontend")
        version: Server version string
        instructions: Server instructions for AI agents
    
    Returns:
        Configured MCP Server instance
    """
    return Server(
        name=name,
        version=version,
        instructions=instructions,
        website_url="https://rationalbloks.com",
        icons=[
            Icon(src="https://rationalbloks.com/logo.svg", mimeType="image/svg+xml"),
            Icon(src="https://rationalbloks.com/logo.png", mimeType="image/png", sizes=["128x128"]),
        ],
    )


class BaseMCPServer:
    """Base MCP server with shared infrastructure.
    
    Provides:
    - Server initialization
    - Common handlers (prompts, resources)
    - Transport layer (STDIO + HTTP)
    - Authentication utilities
    
    Subclasses add:
    - Mode-specific tools
    - Mode-specific tool handlers
    """
    
    def __init__(
        self,
        name: str,
        version: str,
        instructions: str,
        api_key: str | None = None,
        http_mode: bool = False,
    ) -> None:
        """Initialize base MCP server.
        
        Args:
            name: Server name for MCP protocol
            version: Server version string
            instructions: Instructions for AI agents
            api_key: API key (required for STDIO mode)
            http_mode: If True, API key extracted per-request
        """
        self.name = name
        self.version = version
        self.instructions = instructions
        self.http_mode = http_mode
        self._api_key_cache = APIKeyCache()
        
        # Validate API key for STDIO mode
        if not http_mode:
            is_valid, error = validate_api_key(api_key)
            if not is_valid:
                raise ValueError(error)
            self.api_key = api_key
        else:
            self.api_key = None
        
        # Create MCP server instance
        self.server = create_mcp_server(name, version, instructions)
        
        # Tools and handlers (set by subclass)
        self._tools: list[dict] = []
        self._tool_handlers: dict[str, Callable] = {}
        self._prompts: list[Prompt] = []
        self._prompt_handlers: dict[str, Callable] = {}
        
        # Resources
        self._static_resources: dict[str, str] = {
            "rationalbloks://docs/getting-started": DOCS_GETTING_STARTED,
            "rationalbloks://docs/schema-reference": DOCS_SCHEMA_REFERENCE,
            "rationalbloks://docs/api-reference": DOCS_API_REFERENCE,
        }
    
    def register_tools(self, tools: list[dict]) -> None:
        """Register tools for this server mode."""
        self._tools.extend(tools)
    
    def register_tool_handler(self, name: str, handler: Callable) -> None:
        """Register a handler function for a tool."""
        self._tool_handlers[name] = handler
    
    def register_prompts(self, prompts: list[Prompt]) -> None:
        """Register prompts for this server mode."""
        self._prompts.extend(prompts)
    
    def register_prompt_handler(self, name: str, handler: Callable) -> None:
        """Register a handler function for a prompt."""
        self._prompt_handlers[name] = handler
    
    def setup_handlers(self) -> None:
        """Set up all MCP protocol handlers.
        
        Call this AFTER registering tools and prompts.
        """
        self._setup_tool_handlers()
        self._setup_prompt_handlers()
        self._setup_resource_handlers()
    
    def _setup_tool_handlers(self) -> None:
        """Set up tool listing and execution handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            tools_list = []
            for tool in self._tools:
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
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            valid_tools = [t["name"] for t in self._tools]
            if name not in valid_tools:
                raise ValueError(f"Unknown tool: {name}")
            
            handler = self._tool_handlers.get(name)
            if not handler:
                raise ValueError(f"No handler registered for tool: {name}")
            
            try:
                result = await handler(name, arguments)
                formatted = json.dumps(result, indent=2, default=str)
                return [TextContent(type="text", text=formatted)]
            except Exception as e:
                print(f"[rationalbloks-mcp] Error in {name}: {e}", file=sys.stderr)
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _setup_prompt_handlers(self) -> None:
        """Set up prompt listing and execution handlers."""
        
        @self.server.list_prompts()
        async def list_prompts() -> list[Prompt]:
            return self._prompts
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> GetPromptResult:
            handler = self._prompt_handlers.get(name)
            if not handler:
                raise ValueError(f"Unknown prompt: {name}")
            return handler(name, arguments)
    
    def _setup_resource_handlers(self) -> None:
        """Set up resource listing and reading handlers."""
        
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            resources = []
            for uri, _ in self._static_resources.items():
                name = uri.split("/")[-1].replace("-", " ").title()
                resources.append(Resource(
                    uri=uri,
                    name=f"{name} Guide",
                    description=f"Documentation: {name}",
                    mimeType="text/markdown"
                ))
            return resources
        
        @self.server.read_resource()
        async def read_resource(uri) -> str:
            uri_str = str(uri)
            if uri_str in self._static_resources:
                return self._static_resources[uri_str]
            raise ValueError(f"Unknown resource: {uri_str}")
    
    def get_api_key_for_request(self) -> str | None:
        """Get API key for current request.
        
        STDIO mode: Returns stored API key
        HTTP mode: Extracts from Authorization header
        """
        if not self.http_mode:
            return self.api_key
        
        # HTTP mode - extract from request
        ctx = getattr(self.server, 'request_context', None)
        if ctx is None:
            return None
        
        request = getattr(ctx, 'request', None)
        if request is None or not isinstance(request, Request):
            return None
        
        return extract_api_key_from_request(request)
    
    def get_init_options(self) -> InitializationOptions:
        """Get MCP initialization options."""
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
        """Run the MCP server with specified transport.
        
        Args:
            transport: "stdio" for local IDEs or "http" for cloud
        """
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
