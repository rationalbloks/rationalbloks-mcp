# ============================================================================
# RATIONALBLOKS MCP - FRONTEND TOOLS
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# 5 Frontend tools for frontend generation:
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

from ..core import BaseMCPServer
from .client import FrontendClient

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

Updates the .env file with VITE_API_URL pointing to your RationalBloks backend.

USAGE:
1. Clone template with clone_template
2. Create backend with create_backend (note the API URL)
3. Run configure_api_url with the project path and API URL

EXAMPLE:
- project_path: ~/projects/my-app
- api_url: https://my-project.customersblok.rationalbloks.com

This updates .env with:
VITE_API_URL=https://my-project.customersblok.rationalbloks.com""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to the cloned frontend project"
                },
                "api_url": {
                    "type": "string",
                    "description": "Backend API URL from create_backend"
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
    """Frontend MCP server with 5 frontend generation tools.
    
    Extends BaseMCPServer with frontend-specific:
    - Template cloning and exploration
    - Backend integration
    - Frontend configuration
    """
    
    INSTRUCTIONS = """RationalBloks MCP Server - Frontend Mode

Generate frontend applications from the rationalbloksfront template.

WORKFLOW:
1. clone_template - Clone the template to local directory
2. create_backend - Create backend API (optional but recommended)
3. configure_api_url - Connect frontend to backend
4. npm install && npm run dev

Available: 5 frontend tools for template and configuration."""
    
    def __init__(
        self,
        api_key: str | None = None,
        http_mode: bool = False,
    ) -> None:
        """Initialize frontend MCP server."""
        super().__init__(
            name="rationalbloks-frontend",
            version="1.0.0",
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
        """Get frontend client with current API key."""
        api_key = self.get_api_key_for_request()
        return FrontendClient(api_key)
    
    async def _handle_frontend_tool(self, name: str, arguments: dict) -> Any:
        """Handle all frontend tool calls."""
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
        """Handle create-fullstack-app prompt."""
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
    """Factory function to create a frontend MCP server.
    
    Args:
        api_key: API key (required for create_backend)
        http_mode: If True, API key extracted per-request
    
    Returns:
        Configured FrontendMCPServer instance
    """
    return FrontendMCPServer(api_key=api_key, http_mode=http_mode)
