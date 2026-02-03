# ============================================================================
# RATIONALBLOKS MCP - Unified Entry Point
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Unified MCP server supporting 3 modes:
#   - backend:  18 API/database tools (projects, schemas, deployments)
#   - frontend: 14 frontend generation tools (types, views, forms, scaffold)
#   - full:     All 32 tools combined (DEFAULT)
#
# Usage:
#   export RATIONALBLOKS_API_KEY=rb_sk_your_key_here
#   export RATIONALBLOKS_MODE=full  # or backend, frontend
#   rationalbloks-mcp
#
# Entry Points:
#   rationalbloks-mcp          - Uses RATIONALBLOKS_MODE (default: full)
#   rationalbloks-mcp-backend  - Backend mode only
#   rationalbloks-mcp-frontend - Frontend mode only
#
# Environment Variables:
#   RATIONALBLOKS_API_KEY - Your API key (required for STDIO mode)
#   RATIONALBLOKS_MODE    - Mode: backend, frontend, full (default: full)
#   TRANSPORT             - Transport: stdio (default) or http
# ============================================================================

import os
import sys
from typing import Literal

# Version from package metadata
from importlib.metadata import version as _get_version
__version__ = _get_version("rationalbloks-mcp")

# Mode type
Mode = Literal["backend", "frontend", "full"]

# Public API
__all__ = [
    "__version__",
    "main",
    "main_backend",
    "main_frontend",
    "Mode",
]


def _get_mode() -> Mode:
    # Get mode from environment variable
    # Returns: Mode string: "backend", "frontend", or "full"
    mode = os.environ.get("RATIONALBLOKS_MODE", "full").lower()
    if mode not in ("backend", "frontend", "full"):
        print(f"WARNING: Invalid RATIONALBLOKS_MODE '{mode}', using 'full'", file=sys.stderr)
        mode = "full"
    return mode  # type: ignore


def _validate_api_key(api_key: str | None, transport: str) -> str | None:
    # Validate API key for the given transport
    # HTTP mode: API key provided per-request (returns None)
    # STDIO mode: API key required at startup (returns validated key)
    # Raises SystemExit if API key invalid for STDIO mode
    # HTTP mode: API key provided per-request
    if transport == "http":
        return None
    
    # STDIO mode: API key required at startup
    if not api_key:
        print("ERROR: RATIONALBLOKS_API_KEY environment variable not set", file=sys.stderr)
        print("", file=sys.stderr)
        print("Get your API key from: https://rationalbloks.com/settings", file=sys.stderr)
        print("", file=sys.stderr)
        print("Then set it:", file=sys.stderr)
        print("  export RATIONALBLOKS_API_KEY=rb_sk_your_key_here", file=sys.stderr)
        sys.exit(1)
    
    if not api_key.startswith("rb_sk_"):
        print("ERROR: Invalid API key format. Must start with 'rb_sk_'", file=sys.stderr)
        sys.exit(1)
    
    return api_key


def _run_server(mode: Mode) -> None:
    # Run MCP server in the specified mode
    # mode: "backend", "frontend", or "full"
    api_key = os.environ.get("RATIONALBLOKS_API_KEY")
    transport = os.environ.get("TRANSPORT", "stdio").lower()
    http_mode = transport == "http"
    
    # Validate API key
    validated_key = _validate_api_key(api_key, transport)
    
    try:
        if mode == "backend":
            from .backend import create_backend_server
            server = create_backend_server(api_key=validated_key, http_mode=http_mode)
        elif mode == "frontend":
            from .frontend import create_frontend_server
            server = create_frontend_server(api_key=validated_key, http_mode=http_mode)
        else:  # full mode
            server = _create_full_server(api_key=validated_key, http_mode=http_mode)
        
        server.run(transport=transport)
        
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def _create_full_server(api_key: str | None, http_mode: bool):
    # Create a full server with all 32 tools
    # Combines backend (18 tools) + frontend (14 tools)
    from .core import BaseMCPServer
    from .backend.tools import BACKEND_TOOLS, BACKEND_PROMPTS
    from .backend.client import LogicBlokClient
    from .frontend.tools import FRONTEND_TOOLS, FRONTEND_PROMPTS
    from .frontend.client import FrontendClient
    from .frontend.app_generator import AppGenerator
    
    FULL_INSTRUCTIONS = """RationalBloks MCP Server - Full Mode

🚀 BUILD COMPLETE FULLSTACK APPS IN MINUTES

RECOMMENDED WORKFLOW:
1. Already have a project? Use scaffold_frontend (generates all code from schema)
2. Need to clone first? Use clone_template, then scaffold_frontend
3. Starting from zero? Use create_app (clones + creates backend + scaffolds)

FRONTEND GENERATION TOOLS (14 tools):
🔧 Granular Tools (work on YOUR existing project):
- generate_types: TypeScript interfaces from schema
- generate_api_service: API client with CRUD operations  
- generate_entity_view: List view for ONE entity
- generate_entity_form: Create/edit form for ONE entity
- generate_all_views: All views for all entities
- generate_dashboard: Dashboard with stats
- update_routes: Wire up routes in App.tsx
- update_navbar: Update navigation links

🚀 Scaffold Tools:
- scaffold_frontend: Apply ALL generators to existing project
- create_app: Full automation (clone + backend + scaffold)

🔌 Utility Tools:
- clone_template, configure_api_url, create_backend, get_template_structure

BACKEND TOOLS (18 tools):
- Project management: list_projects, get_project, create_project, etc.
- Schema operations: get_schema, update_schema
- Deployment: deploy_staging, deploy_production, rollback_project

SCHEMA FORMAT (FLAT - CRITICAL):
✅ {tasks: {title: {type: "string", max_length: 200}}} 
❌ {tasks: {fields: {title: {type: "string"}}}}

AVAILABLE: 32 tools (18 backend + 14 frontend)"""
    
    class FullMCPServer(BaseMCPServer):
        # Full MCP server with all 24 tools
        
        def __init__(self, api_key: str | None, http_mode: bool):
            super().__init__(
                name="rationalbloks",
                version=__version__,
                instructions=FULL_INSTRUCTIONS,
                api_key=api_key,
                http_mode=http_mode,
            )
            
            # Register all tools
            self.register_tools(BACKEND_TOOLS)
            self.register_tools(FRONTEND_TOOLS)
            
            # Register all prompts
            self.register_prompts(BACKEND_PROMPTS)
            self.register_prompts(FRONTEND_PROMPTS)
            
            # Register handlers
            self.register_tool_handler("*", self._handle_tool)
            
            # Set up MCP handlers
            self.setup_handlers()
        
        def _get_backend_client(self) -> LogicBlokClient:
            api_key = self.get_api_key_for_request()
            if not api_key:
                raise ValueError("No API key available")
            return LogicBlokClient(api_key)
        
        def _get_frontend_client(self) -> FrontendClient:
            api_key = self.get_api_key_for_request()
            return FrontendClient(api_key)
        
        def _get_app_generator(self) -> AppGenerator:
            api_key = self.get_api_key_for_request()
            if not api_key:
                raise ValueError("API key required for create_app")
            return AppGenerator(api_key)
        
        async def _handle_tool(self, name: str, arguments: dict):
            # Route tool calls to appropriate client
            # Backend tools
            backend_tool_names = [t["name"] for t in BACKEND_TOOLS]
            if name in backend_tool_names:
                async with self._get_backend_client() as client:
                    return await self._call_backend_tool(client, name, arguments)
            
            # Frontend tools - special handling for create_app
            frontend_tool_names = [t["name"] for t in FRONTEND_TOOLS]
            if name in frontend_tool_names:
                if name == "create_app":
                    return await self._call_create_app(arguments)
                async with self._get_frontend_client() as client:
                    return await self._call_frontend_tool(client, name, arguments)
            
            raise ValueError(f"Unknown tool: {name}")
        
        async def _call_create_app(self, args: dict):
            # Handle create_app with AppGenerator
            generator = self._get_app_generator()
            return await generator.create_app(
                name=args["name"],
                description=args["description"],
                destination=args["destination"],
                schema=args["schema"],
                wait_for_deployment=args.get("wait_for_deployment", True),
                run_npm_install=args.get("run_npm_install", True),
            )
        
        async def _call_backend_tool(self, client: LogicBlokClient, name: str, args: dict):
            # Call a backend tool
            if name == "list_projects":
                return await client.list_projects()
            elif name == "get_project":
                return await client.get_project(args["project_id"])
            elif name == "get_schema":
                return await client.get_schema(args["project_id"])
            elif name == "get_user_info":
                return await client.get_user_info()
            elif name == "get_job_status":
                return await client.get_job_status(args["job_id"])
            elif name == "get_project_info":
                return await client.get_project_info(args["project_id"])
            elif name == "get_version_history":
                return await client.get_version_history(args["project_id"])
            elif name == "get_template_schemas":
                return await client.get_template_schemas()
            elif name == "get_subscription_status":
                return await client.get_subscription_status()
            elif name == "get_project_usage":
                return await client.get_project_usage(args["project_id"])
            elif name == "get_schema_at_version":
                return await client.get_schema_at_version(args["project_id"], args["version"])
            elif name == "create_project":
                return await client.create_project(
                    name=args["name"],
                    schema=args["schema"],
                    description=args.get("description"),
                )
            elif name == "update_schema":
                return await client.update_schema(args["project_id"], args["schema"])
            elif name == "deploy_staging":
                return await client.deploy_staging(args["project_id"])
            elif name == "deploy_production":
                return await client.deploy_production(args["project_id"])
            elif name == "delete_project":
                return await client.delete_project(args["project_id"])
            elif name == "rollback_project":
                return await client.rollback_project(
                    project_id=args["project_id"],
                    version=args["version"],
                    environment=args.get("environment", "staging"),
                )
            elif name == "rename_project":
                return await client.rename_project(args["project_id"], args["name"])
            else:
                raise ValueError(f"Unknown backend tool: {name}")
        
        async def _call_frontend_tool(self, client: FrontendClient, name: str, args: dict):
            # Call a frontend tool
            # Generation tools
            if name == "generate_types":
                return await client.generate_types(
                    project_path=args["project_path"],
                    schema=args["schema"],
                )
            elif name == "generate_api_service":
                return await client.generate_api_service(
                    project_path=args["project_path"],
                    schema=args["schema"],
                    api_url=args.get("api_url"),
                )
            elif name == "generate_entity_view":
                return await client.generate_entity_view(
                    project_path=args["project_path"],
                    table_name=args["table_name"],
                    fields=args["fields"],
                )
            elif name == "generate_entity_form":
                return await client.generate_entity_form(
                    project_path=args["project_path"],
                    table_name=args["table_name"],
                    fields=args["fields"],
                )
            elif name == "generate_all_views":
                return await client.generate_all_views(
                    project_path=args["project_path"],
                    schema=args["schema"],
                )
            elif name == "generate_dashboard":
                return await client.generate_dashboard(
                    project_path=args["project_path"],
                    app_name=args["app_name"],
                    schema=args["schema"],
                )
            elif name == "update_routes":
                return await client.update_routes(
                    project_path=args["project_path"],
                    schema=args["schema"],
                )
            elif name == "update_navbar":
                return await client.update_navbar(
                    project_path=args["project_path"],
                    app_name=args["app_name"],
                    schema=args["schema"],
                )
            # Scaffold tool
            elif name == "scaffold_frontend":
                return await client.scaffold_frontend(
                    project_path=args["project_path"],
                    app_name=args["app_name"],
                    schema=args["schema"],
                    api_url=args.get("api_url"),
                )
            # Utility tools
            elif name == "clone_template":
                return await client.clone_template(
                    destination=args["destination"],
                    project_name=args["project_name"],
                )
            elif name == "get_template_structure":
                return await client.get_template_structure(
                    path=args.get("path", ""),
                    max_depth=args.get("max_depth", 3),
                )
            elif name == "create_backend":
                return await client.create_backend(
                    name=args["name"],
                    schema=args["schema"],
                    description=args.get("description"),
                )
            elif name == "configure_api_url":
                return await client.configure_api_url(
                    project_path=args["project_path"],
                    api_url=args["api_url"],
                )
            else:
                raise ValueError(f"Unknown frontend tool: {name}")
    
    return FullMCPServer(api_key=api_key, http_mode=http_mode)


# ============================================================================
# ENTRY POINTS
# ============================================================================

def main() -> None:
    # Main entry point - uses RATIONALBLOKS_MODE environment variable
    # Default mode is 'full' (all 32 tools: 18 backend + 14 frontend)
    mode = _get_mode()
    print(f"[rationalbloks-mcp] Starting in {mode} mode...", file=sys.stderr)
    _run_server(mode)


def main_backend() -> None:
    # Backend-only entry point (18 tools)
    print("[rationalbloks-mcp] Starting in backend mode...", file=sys.stderr)
    _run_server("backend")


def main_frontend() -> None:
    # Frontend-only entry point (14 tools)
    print("[rationalbloks-mcp] Starting in frontend mode...", file=sys.stderr)
    _run_server("frontend")


if __name__ == "__main__":
    main()
