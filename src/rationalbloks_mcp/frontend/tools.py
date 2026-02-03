# ============================================================================
# RATIONALBLOKS MCP - FRONTEND TOOLS
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# 6 Frontend tools for frontend generation:
# - create_app: MAIN TOOL - Creates complete app from schema (end-to-end)
# - clone_template: Clone rationalbloksfront template
# - get_template_structure: Explore template file structure
# - read_template_file: Read file from template
# - create_backend: Create backend via Backend MCP
# - configure_api_url: Set API URL in frontend .env
# ============================================================================

import os
import sys
from typing import Any

from mcp.types import Prompt, PromptArgument, PromptMessage, GetPromptResult, TextContent

from .. import __version__
from ..core import BaseMCPServer
from .client import FrontendClient
from .app_generator import AppGenerator

# Public API
__all__ = [
    "FRONTEND_TOOLS",
    "FrontendMCPServer",
    "create_frontend_server",
]


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

FRONTEND_TOOLS = [
    # ========================================================================
    # MAIN TOOL - create_app (the complete automation)
    # ========================================================================
    {
        "name": "create_app",
        "title": "Create Complete App",
        "description": """🚀 CREATE A COMPLETE WORKING APPLICATION IN ONE STEP

This is the main tool that transforms a template into a fully functional app.
It handles EVERYTHING: backend creation, frontend generation, configuration.

WHAT IT DOES (13 automated steps):
1. Clone the rationalbloksfront template
2. Create backend API from your schema
3. Wait for backend deployment (2-5 minutes)
4. Generate TypeScript types from schema
5. Generate API service with CRUD operations
6. Generate list views for each entity
7. Generate create/edit forms for each entity
8. Generate dashboard with entity stats
9. Update routes in App.tsx
10. Update Navbar with navigation
11. Remove template-specific files
12. Update package.json with app info
13. Run npm install

SCHEMA FORMAT (FLAT - CRITICAL):
{
  "tasks": {
    "title": {"type": "string", "max_length": 200, "required": true},
    "description": {"type": "text"},
    "status": {"type": "string", "enum": ["pending", "in_progress", "completed"], "default": "pending"},
    "due_date": {"type": "date"}
  }
}

⚠️ SCHEMA RULES:
- FLAT format: table → field → properties (NO "fields" nesting!)
- string: MUST have max_length
- decimal: MUST have precision and scale
- Use "datetime" NOT "timestamp"
- DON'T define: id, created_at, updated_at (automatic)
- DON'T create users/customers tables (use app_users)

AFTER COMPLETION:
- cd into project directory
- npm run dev
- Open http://localhost:5173
- Login and start using your app!

RESULT:
Returns project path, backend URL, list of generated files, and any errors.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Application name (e.g., 'TaskManager', 'InventoryApp')"
                },
                "description": {
                    "type": "string",
                    "description": "What the app does (used for backend project)"
                },
                "destination": {
                    "type": "string",
                    "description": "Parent directory to create project in (e.g., '~/projects' or 'C:/Projects')"
                },
                "schema": {
                    "type": "object",
                    "description": "Backend schema in FLAT format. Every field MUST have 'type'. Use get_template_schemas to see examples."
                },
                "wait_for_deployment": {
                    "type": "boolean",
                    "description": "Wait for backend to deploy before continuing (default: true, takes 2-5 min)"
                },
                "run_npm_install": {
                    "type": "boolean",
                    "description": "Run npm install after generation (default: true)"
                }
            },
            "required": ["name", "description", "destination", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
    },
    # ========================================================================
    # INDIVIDUAL TOOLS (for granular control)
    # ========================================================================
    {
        "name": "clone_template",
        "title": "Clone Template",
        "description": """Clone the rationalbloksfront template to create a new frontend project. 
        
This tool clones the official RationalBloks frontend template from GitHub to your local filesystem.

WHAT IT DOES:
1. Clones https://github.com/rationalbloks/rationalbloksfront
2. Removes .git directory for fresh start
3. Initializes new git repository
4. Returns file structure and next steps

USAGE:
- destination: Parent directory (e.g., "~/projects" or "C:/Projects")
- project_name: Name for your project folder (e.g., "my-app")

AFTER CLONING:
1. cd into the project directory
2. npm install
3. Use configure_api_url to set your backend API
4. npm run dev""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "Parent directory to clone into (e.g., ~/projects)"
                },
                "project_name": {
                    "type": "string",
                    "description": "Name for the project folder"
                }
            },
            "required": ["destination", "project_name"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}
    },
    {
        "name": "get_template_structure",
        "title": "Get Template Structure",
        "description": """Explore the file structure of the rationalbloksfront template.

Returns a tree view of the template's directory structure, highlighting key files:
- src/: Source code (components, pages, hooks, services)
- public/: Static assets
- Configuration files (vite.config.ts, tsconfig.json, etc.)

Use this to understand the template before cloning or to plan modifications.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Subdirectory to explore (empty for root)"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum directory depth (default: 3)"
                }
            },
            "required": []
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
    },
    {
        "name": "read_template_file",
        "title": "Read Template File",
        "description": """Read a specific file from the rationalbloksfront template.

Useful for:
- Examining configuration files before cloning
- Understanding the template structure
- Planning customizations

Note: For full file access, use clone_template first.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file within the template (e.g., 'src/App.tsx')"
                }
            },
            "required": ["file_path"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
    },
    {
        "name": "create_backend",
        "title": "Create Backend",
        "description": """Create a backend API project using the RationalBloks Backend MCP.

This is a convenience wrapper around the backend's create_project tool.

SCHEMA FORMAT (FLAT):
{
  "users": {
    "email": {"type": "string", "required": true, "unique": true},
    "name": {"type": "string", "required": true}
  }
}

⚠️ DO NOT nest fields under a 'fields' key!

WORKFLOW:
1. Create frontend with clone_template
2. Create backend with create_backend
3. Connect with configure_api_url
4. npm run dev""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Project name"
                },
                "schema": {
                    "type": "object",
                    "description": "JSON schema in FLAT format"
                },
                "description": {
                    "type": "string",
                    "description": "Optional project description"
                }
            },
            "required": ["name", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}
    },
    {
        "name": "configure_api_url",
        "title": "Configure API URL",
        "description": """Configure the backend API URL in a cloned frontend project.

Updates the .env file with VITE_DATABASE_API_URL pointing to your RationalBloks backend.

USAGE:
1. Clone template with clone_template
2. Create backend with create_backend (note the staging URL)
3. Run configure_api_url with the project path and staging URL

EXAMPLE:
- project_path: ~/projects/my-app
- api_url: https://abc123-staging.customersblok.rationalbloks.com

This updates .env with:
VITE_DATABASE_API_URL=https://abc123-staging.customersblok.rationalbloks.com

NOTE: VITE_BUSINESS_LOGIC_API_URL (for platform auth) is already configured in the template.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to the cloned frontend project"
                },
                "api_url": {
                    "type": "string",
                    "description": "Backend staging URL from create_backend (e.g., https://xxx-staging.customersblok.rationalbloks.com)"
                }
            },
            "required": ["project_path", "api_url"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}
    },
]


# ============================================================================
# FRONTEND PROMPTS
# ============================================================================

FRONTEND_PROMPTS = [
    Prompt(
        name="create-fullstack-app",
        title="Create Fullstack App",
        description="Create a complete fullstack application with frontend and backend",
        arguments=[
            PromptArgument(
                name="app_name",
                description="Name for your application",
                required=True,
            ),
            PromptArgument(
                name="description",
                description="Description of what the app should do",
                required=True,
            ),
            PromptArgument(
                name="destination",
                description="Directory to create the project in",
                required=True,
            ),
        ],
    ),
]


# ============================================================================
# FRONTEND MCP SERVER
# ============================================================================

class FrontendMCPServer(BaseMCPServer):
    # Frontend MCP server with 6 frontend generation tools
    # Extends BaseMCPServer with: Complete app generation, template cloning, backend integration
    
    INSTRUCTIONS = """RationalBloks MCP Server - Frontend Mode

🚀 MAIN TOOL: create_app
Creates a COMPLETE working application in one step:
- Clones template, creates backend, generates views, configures everything
- Just provide: name, description, destination, schema
- Result: Ready-to-run app with npm run dev

INDIVIDUAL TOOLS (for granular control):
- clone_template: Clone template only
- create_backend: Create backend API only
- configure_api_url: Set API URL only
- get_template_structure: Explore template
- read_template_file: Read template files

WORKFLOW with create_app:
1. Use get_template_schemas to see schema examples
2. Call create_app with name, description, destination, schema
3. Wait for completion (2-5 minutes)
4. cd into project && npm run dev

Available: 6 frontend tools for complete app generation."""
    
    def __init__(
        self,
        api_key: str | None = None,
        http_mode: bool = False,
    ) -> None:
        # Initialize frontend MCP server
        super().__init__(
            name="rationalbloks-frontend",
            version=__version__,
            instructions=self.INSTRUCTIONS,
            api_key=api_key,
            http_mode=http_mode,
        )
        
        # Register frontend tools and prompts
        self.register_tools(FRONTEND_TOOLS)
        self.register_prompts(FRONTEND_PROMPTS)
        
        # Register tool handler
        self.register_tool_handler("*", self._handle_frontend_tool)
        
        # Register prompt handlers
        self.register_prompt_handler(
            "create-fullstack-app",
            self._handle_fullstack_prompt,
        )
        
        # Set up MCP handlers
        self.setup_handlers()
    
    def _get_client(self) -> FrontendClient:
        # Get frontend client with current API key
        api_key = self.get_api_key_for_request()
        return FrontendClient(api_key)
    
    def _get_app_generator(self) -> AppGenerator:
        # Get app generator with current API key
        api_key = self.get_api_key_for_request()
        if not api_key:
            raise ValueError("API key required for create_app")
        return AppGenerator(api_key)
    
    async def _handle_frontend_tool(self, name: str, arguments: dict) -> Any:
        # Handle all frontend tool calls
        
        # create_app uses AppGenerator (the main tool)
        if name == "create_app":
            generator = self._get_app_generator()
            return await generator.create_app(
                name=arguments["name"],
                description=arguments["description"],
                destination=arguments["destination"],
                schema=arguments["schema"],
                wait_for_deployment=arguments.get("wait_for_deployment", True),
                run_npm_install=arguments.get("run_npm_install", True),
            )
        
        # Other tools use FrontendClient
        async with self._get_client() as client:
            if name == "clone_template":
                return await client.clone_template(
                    destination=arguments["destination"],
                    project_name=arguments["project_name"],
                )
            elif name == "get_template_structure":
                return await client.get_template_structure(
                    path=arguments.get("path", ""),
                    max_depth=arguments.get("max_depth", 3),
                )
            elif name == "read_template_file":
                return await client.read_template_file(
                    file_path=arguments["file_path"],
                )
            elif name == "create_backend":
                return await client.create_backend(
                    name=arguments["name"],
                    schema=arguments["schema"],
                    description=arguments.get("description"),
                )
            elif name == "configure_api_url":
                return await client.configure_api_url(
                    project_path=arguments["project_path"],
                    api_url=arguments["api_url"],
                )
            else:
                raise ValueError(f"Unknown frontend tool: {name}")
    
    def _handle_fullstack_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        # Handle create-fullstack-app prompt
        app_name = arguments.get("app_name", "my-app") if arguments else "my-app"
        description = arguments.get("description", "") if arguments else ""
        destination = arguments.get("destination", "~/projects") if arguments else "~/projects"
        
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Create a fullstack app called "{app_name}" in {destination}.

App description: {description}

STEPS:
1. Use clone_template to clone the frontend template
2. Analyze the description to design a database schema
3. Use create_backend with the schema to create the API
4. Use configure_api_url to connect frontend to backend
5. Provide instructions for running the app

Remember:
- Schema must be in FLAT format (no 'fields' nesting)
- Every field needs a 'type' property
- Use get_template_schemas from backend to see examples

Start now:""",
                    ),
                )
            ]
        )


def create_frontend_server(
    api_key: str | None = None,
    http_mode: bool = False,
) -> FrontendMCPServer:
    # Factory function to create a frontend MCP server
    # Returns: Configured FrontendMCPServer instance
    return FrontendMCPServer(api_key=api_key, http_mode=http_mode)
