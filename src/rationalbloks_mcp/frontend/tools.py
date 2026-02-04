# ============================================================================
# RATIONALBLOKS MCP - FRONTEND TOOLS
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# 14 Frontend tools using THE ONE WAY ARCHITECTURE:
# - @rationalbloks/universalfront: createAuthApi for auth + tokens
# - @rationalbloks/frontbuilderblok: initApi + getApi for generic CRUD
#
# All generated code uses the pattern:
#   const authApi = createAuthApi(API_URL);
#   initApi(authApi);
#   export { authApi, getApi };
#   export const ENTITIES = { TASKS: "tasks" } as const;
#
# GENERATION TOOLS (work on any existing project):
# - generate_types: Generate TypeScript types from schema
# - generate_api_service: Generate appApi.ts with THE ONE WAY pattern
# - generate_entity_view: Generate list view using getApi().getAll()
# - generate_entity_form: Generate form using getApi().create/update()
# - generate_dashboard: Generate dashboard with entity stats
# - generate_all_views: Generate all views for all entities
# - update_routes: Add routes to App.tsx
# - update_navbar: Update navigation config
#
# SCAFFOLD TOOLS:
# - scaffold_frontend: Apply all generators to existing project (no clone)
# - create_app: Full automation including clone + backend creation
#
# UTILITY TOOLS:
# - clone_template: Clone rationalbloksfront from GitHub
# - configure_api_url: Set API URL in .env
# - create_backend: Create backend via Backend MCP
# - get_template_structure: Explore template structure
# ============================================================================

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
    # GENERATION TOOLS - Work on ANY existing project
    # ========================================================================
    {
        "name": "generate_types",
        "title": "Generate TypeScript Types",
        "description": """Generate TypeScript interfaces from a database schema.

Creates src/types/generated.ts with:
- Interface for each entity (e.g., Task, Project)
- CreateInput and UpdateInput types for forms
- Proper type mapping (string, number, boolean, etc.)

WORKS ON ANY PROJECT - just point to your project directory.

EXAMPLE OUTPUT:
```typescript
export interface Task {
  id: string;
  title: string;
  status?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTaskInput {
  title: string;
  status?: string;
}

export type UpdateTaskInput = Partial<CreateTaskInput>;
```

USE WHEN:
- You have a schema and need TypeScript types
- Your backend schema changed and you need to regenerate types
- Starting a new frontend from an existing rationalbloksfront template""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to your frontend project (e.g., 'C:/projects/my-app')"
                },
                "schema": {
                    "type": "object",
                    "description": "Database schema in FLAT format: {table: {field: {type, ...}}}"
                }
            },
            "required": ["project_path", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "generate_api_service",
        "title": "Generate API Service",
        "description": """Generate API service using THE ONE WAY pattern from npm packages.

Creates src/services/appApi.ts with:
- createAuthApi from @rationalbloks/universalfront (auth + tokens)
- initApi + getApi from @rationalbloks/frontbuilderblok (generic CRUD)
- ENTITIES constant for type-safe entity names

THE ONE WAY PATTERN:
All CRUD operations are handled generically by frontbuilderblok - no per-entity methods needed!

EXAMPLE OUTPUT:
```typescript
import { createAuthApi } from "@rationalbloks/universalfront";
import { initApi, getApi } from "@rationalbloks/frontbuilderblok";

const authApi = createAuthApi(API_URL);
initApi(authApi);

export const ENTITIES = {
  TASKS: "tasks",
  PROJECTS: "projects"
} as const;

export { authApi, getApi };
```

USAGE IN COMPONENTS:
```typescript
import { getApi, ENTITIES } from "../../services/appApi";
const tasks = await getApi().getAll<Task>(ENTITIES.TASKS);
await getApi().create<Task>(ENTITIES.TASKS, data);
```

REQUIRES: @rationalbloks/universalfront and @rationalbloks/frontbuilderblok npm packages.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to your frontend project"
                },
                "schema": {
                    "type": "object",
                    "description": "Database schema in FLAT format"
                },
                "api_url": {
                    "type": "string",
                    "description": "Backend API URL (optional - will use VITE_DATABASE_API_URL env var if not provided)"
                }
            },
            "required": ["project_path", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "generate_entity_view",
        "title": "Generate Entity View",
        "description": """Generate a list view component for ONE entity using THE ONE WAY pattern.

Creates src/components/views/{Entity}View.tsx with:
- Data table with all fields
- Loading and error states
- Edit and Delete actions using getApi().remove()
- "Add New" button
- Uses MUI components

USES THE ONE WAY PATTERN:
```typescript
import { getApi, ENTITIES } from "../../services/appApi";
const data = await getApi().getAll<Task>(ENTITIES.TASKS);
await getApi().remove(ENTITIES.TASKS, id);
```

GRANULAR CONTROL: Generate views one at a time for specific entities.

EXAMPLE: For table "tasks" with fields title, status, due_date:
- Creates TasksView.tsx
- Displays table with columns: Title, Status, Due Date
- Actions: Edit, Delete buttons per row""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to your frontend project"
                },
                "table_name": {
                    "type": "string",
                    "description": "Name of the table/entity (e.g., 'tasks', 'projects')"
                },
                "fields": {
                    "type": "object",
                    "description": "Field definitions for this table: {field_name: {type, required, ...}}"
                }
            },
            "required": ["project_path", "table_name", "fields"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "generate_entity_form",
        "title": "Generate Entity Form",
        "description": """Generate a create/edit form component for ONE entity using THE ONE WAY pattern.

Creates src/components/views/{Entity}FormView.tsx with:
- Form with inputs for all editable fields
- Proper input types (text, number, select for enums, date picker)
- Create mode and Edit mode (based on URL param)
- Form validation
- Submit handling using getApi().create() and getApi().update()

USES THE ONE WAY PATTERN:
```typescript
import { getApi, ENTITIES } from "../../services/appApi";
const data = await getApi().getOne<Task>(ENTITIES.TASKS, id);
await getApi().create<Task>(ENTITIES.TASKS, formData);
await getApi().update<Task>(ENTITIES.TASKS, id, formData);
```

GRANULAR CONTROL: Generate forms one at a time for specific entities.

EXAMPLE: For table "tasks" with fields title (required), status (enum), due_date:
- Creates TaskFormView.tsx
- Text input for title (required)
- Select dropdown for status with enum options
- Date picker for due_date""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to your frontend project"
                },
                "table_name": {
                    "type": "string",
                    "description": "Name of the table/entity (e.g., 'tasks')"
                },
                "fields": {
                    "type": "object",
                    "description": "Field definitions for this table"
                }
            },
            "required": ["project_path", "table_name", "fields"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "generate_all_views",
        "title": "Generate All Views",
        "description": """Generate list views AND form views for ALL entities in schema.

Convenience tool that calls generate_entity_view and generate_entity_form for each table.

Creates:
- {Entity}View.tsx for each table (list view)
- {Entity}FormView.tsx for each table (create/edit form)

USE THIS when you want all views generated at once.
Use generate_entity_view/generate_entity_form for granular control.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to your frontend project"
                },
                "schema": {
                    "type": "object",
                    "description": "Complete database schema in FLAT format"
                }
            },
            "required": ["project_path", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "generate_dashboard",
        "title": "Generate Dashboard",
        "description": """Generate a dashboard view with entity statistics using THE ONE WAY pattern.

Creates src/components/views/DashboardView.tsx with:
- Welcome header with app name
- Stats cards showing count for each entity
- Quick action links to each entity list
- Uses MUI Grid and Card components
- Uses getApi().getAll() for fetching counts""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to your frontend project"
                },
                "app_name": {
                    "type": "string",
                    "description": "Display name for the app (shown in dashboard header)"
                },
                "schema": {
                    "type": "object",
                    "description": "Complete database schema in FLAT format"
                }
            },
            "required": ["project_path", "app_name", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "update_routes",
        "title": "Update Routes",
        "description": """Update App.tsx with routes for all generated views.

Modifies src/App.tsx to include:
- Import statements for all view components
- Route definitions for list views (/{entity})
- Route definitions for create forms (/{entity}/new)
- Route definitions for edit forms (/{entity}/:id/edit)
- Dashboard as default authenticated route

PRESERVES: Auth provider, theme, and other existing setup from universalfront.

RUN THIS after generating views to wire up navigation.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to your frontend project"
                },
                "schema": {
                    "type": "object",
                    "description": "Complete database schema (used to determine routes)"
                }
            },
            "required": ["project_path", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "update_navbar",
        "title": "Update Navbar",
        "description": """Update the navigation bar configuration with app-specific links.

Creates/updates src/config/Navbar.tsx with:
- App name for branding
- Navigation items for Dashboard and each entity
- Proper TypeScript types""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to your frontend project"
                },
                "app_name": {
                    "type": "string",
                    "description": "Display name for the app"
                },
                "schema": {
                    "type": "object",
                    "description": "Complete database schema (used to create nav items)"
                }
            },
            "required": ["project_path", "app_name", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    # ========================================================================
    # SCAFFOLD TOOLS - Apply multiple generators
    # ========================================================================
    {
        "name": "scaffold_frontend",
        "title": "Scaffold Frontend",
        "description": """🚀 APPLY ALL GENERATORS to an existing frontend project.

This is the RECOMMENDED tool when you already have a rationalbloksfront-based project
(cloned template or existing app) and want to generate everything from a schema.

USES THE ONE WAY ARCHITECTURE:
- createAuthApi from @rationalbloks/universalfront (auth + tokens)
- initApi + getApi from @rationalbloks/frontbuilderblok (generic CRUD)
- ENTITIES constant for type-safe entity names
- All CRUD via getApi().getAll(), getApi().create(), etc.

WHAT IT DOES (8 steps on your EXISTING project):
1. Generate TypeScript types (src/types/generated.ts)
2. Generate API service using THE ONE WAY pattern (src/services/appApi.ts)
3. Generate list views for each entity (using getApi().getAll())
4. Generate create/edit forms for each entity (using getApi().create/update())
5. Generate dashboard (using getApi() for stats)
6. Update App.tsx with routes
7. Update Navbar configuration
8. Optionally configure API URL in .env

NO CLONING - works on whatever project you point to.
NO BACKEND CREATION - assumes backend already exists.

USE create_app if you need cloning + backend creation.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to your existing frontend project"
                },
                "app_name": {
                    "type": "string",
                    "description": "Display name for the app"
                },
                "schema": {
                    "type": "object",
                    "description": "Database schema in FLAT format"
                },
                "api_url": {
                    "type": "string",
                    "description": "Backend API URL (optional - set in .env if provided)"
                }
            },
            "required": ["project_path", "app_name", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "create_app",
        "title": "Create Complete App",
        "description": """🚀 CREATE A COMPLETE APPLICATION FROM SCRATCH

Full automation: clone template + create backend + scaffold frontend.
Use this when starting completely fresh with no existing project.

USES THE ONE WAY ARCHITECTURE:
All generated code uses createAuthApi + initApi + getApi from npm packages.
No per-entity CRUD methods generated - everything uses generic getApi() calls.

WHAT IT DOES (13 steps):
1. Clone rationalbloksfront template from GitHub
2. Create backend API from schema (via RationalBloks API)
3. Wait for backend deployment (2-5 minutes)
4. Generate TypeScript types
5. Generate API service (THE ONE WAY pattern)
6. Generate all views (using getApi().getAll())
7. Generate dashboard
8. Update routes
9. Update navbar
10. Cleanup template-specific files
11. Update package.json
12. Configure .env with API URL
13. Run npm install

REQUIRES: Network access to GitHub and RationalBloks API.

PREFER scaffold_frontend if you already have a project.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Application name (e.g., 'TaskManager')"
                },
                "description": {
                    "type": "string",
                    "description": "What the app does"
                },
                "destination": {
                    "type": "string",
                    "description": "Parent directory to create project in"
                },
                "schema": {
                    "type": "object",
                    "description": "Backend schema in FLAT format"
                },
                "wait_for_deployment": {
                    "type": "boolean",
                    "description": "Wait for backend to deploy (default: true)"
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
    # UTILITY TOOLS
    # ========================================================================
    {
        "name": "clone_template",
        "title": "Clone Template",
        "description": """Clone the rationalbloksfront template from GitHub.

Use this to get a fresh copy of the template, then use scaffold_frontend to generate code.

WHAT IT DOES:
1. Clones https://github.com/velosovictor/rationalbloksfront
2. Removes .git directory
3. Initializes new git repository

AFTER CLONING, use scaffold_frontend to generate your app code.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "Parent directory to clone into"
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
        "name": "configure_api_url",
        "title": "Configure API URL",
        "description": """Set the backend API URL in the project's .env file.

Updates VITE_DATABASE_API_URL to point to your RationalBloks backend.
Creates .env from .env.example if needed.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to the frontend project"
                },
                "api_url": {
                    "type": "string",
                    "description": "Backend API URL"
                }
            },
            "required": ["project_path", "api_url"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False}
    },
    {
        "name": "create_backend",
        "title": "Create Backend",
        "description": """Create a backend API project via RationalBloks.

Wrapper around the backend create_project tool.
Returns project_id and staging URL for use with configure_api_url.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Project name"
                },
                "schema": {
                    "type": "object",
                    "description": "Database schema in FLAT format"
                },
                "description": {
                    "type": "string",
                    "description": "Project description"
                }
            },
            "required": ["name", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True}
    },
    {
        "name": "get_template_structure",
        "title": "Get Template Structure",
        "description": """Get the file structure of the rationalbloksfront template.

Returns a tree view of key directories and files.
Useful for understanding the template before using it.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Subdirectory to explore (empty for root)"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum depth (default: 3)"
                }
            },
            "required": []
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
    },
]


# ============================================================================
# FRONTEND PROMPTS
# ============================================================================

FRONTEND_PROMPTS = [
    Prompt(
        name="scaffold-from-schema",
        title="Scaffold Frontend from Schema",
        description="Generate frontend code for an existing project using a schema",
        arguments=[
            PromptArgument(
                name="project_path",
                description="Path to your existing frontend project",
                required=True,
            ),
            PromptArgument(
                name="app_name",
                description="Display name for your app",
                required=True,
            ),
        ],
    ),
    Prompt(
        name="create-fullstack-app",
        title="Create Fullstack App",
        description="Create a complete fullstack application from scratch",
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
    """Frontend MCP server with 14 tools for flexible frontend generation."""
    
    INSTRUCTIONS = """RationalBloks MCP Server - Frontend Mode

🔧 GENERATION TOOLS (work on YOUR existing project):
- generate_types: TypeScript interfaces from schema
- generate_api_service: API client with CRUD operations
- generate_entity_view: List view for ONE entity
- generate_entity_form: Create/edit form for ONE entity  
- generate_all_views: All views for all entities
- generate_dashboard: Dashboard with stats
- update_routes: Wire up routes in App.tsx
- update_navbar: Update navigation links

🚀 SCAFFOLD TOOLS:
- scaffold_frontend: Apply ALL generators to existing project (RECOMMENDED)
- create_app: Full automation from scratch (clone + backend + scaffold)

🔌 UTILITY TOOLS:
- clone_template: Get fresh template from GitHub
- configure_api_url: Set .env API URL
- create_backend: Create backend via API
- get_template_structure: Explore template

RECOMMENDED WORKFLOW:
1. Already have a project? Use scaffold_frontend
2. Need to clone first? Use clone_template, then scaffold_frontend
3. Starting from zero? Use create_app

Available: 14 frontend tools for maximum flexibility."""
    
    def __init__(
        self,
        api_key: str | None = None,
        http_mode: bool = False,
    ) -> None:
        super().__init__(
            name="rationalbloks-frontend",
            version=__version__,
            instructions=self.INSTRUCTIONS,
            api_key=api_key,
            http_mode=http_mode,
        )
        
        self.register_tools(FRONTEND_TOOLS)
        self.register_prompts(FRONTEND_PROMPTS)
        self.register_tool_handler("*", self._handle_frontend_tool)
        self.register_prompt_handler("scaffold-from-schema", self._handle_scaffold_prompt)
        self.register_prompt_handler("create-fullstack-app", self._handle_fullstack_prompt)
        self.setup_handlers()
    
    def _get_client(self) -> FrontendClient:
        api_key = self.get_api_key_for_request()
        return FrontendClient(api_key)
    
    def _get_app_generator(self) -> AppGenerator:
        api_key = self.get_api_key_for_request()
        if not api_key:
            raise ValueError("API key required for create_app")
        return AppGenerator(api_key)
    
    async def _handle_frontend_tool(self, name: str, arguments: dict) -> Any:
        # Handle all frontend tool calls
        
        # Create app uses AppGenerator (full automation)
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
        
        # All other tools use FrontendClient
        async with self._get_client() as client:
            # Generation tools
            if name == "generate_types":
                return await client.generate_types(
                    project_path=arguments["project_path"],
                    schema=arguments["schema"],
                )
            elif name == "generate_api_service":
                return await client.generate_api_service(
                    project_path=arguments["project_path"],
                    schema=arguments["schema"],
                    api_url=arguments.get("api_url"),
                )
            elif name == "generate_entity_view":
                return await client.generate_entity_view(
                    project_path=arguments["project_path"],
                    table_name=arguments["table_name"],
                    fields=arguments["fields"],
                )
            elif name == "generate_entity_form":
                return await client.generate_entity_form(
                    project_path=arguments["project_path"],
                    table_name=arguments["table_name"],
                    fields=arguments["fields"],
                )
            elif name == "generate_all_views":
                return await client.generate_all_views(
                    project_path=arguments["project_path"],
                    schema=arguments["schema"],
                )
            elif name == "generate_dashboard":
                return await client.generate_dashboard(
                    project_path=arguments["project_path"],
                    app_name=arguments["app_name"],
                    schema=arguments["schema"],
                )
            elif name == "update_routes":
                return await client.update_routes(
                    project_path=arguments["project_path"],
                    schema=arguments["schema"],
                )
            elif name == "update_navbar":
                return await client.update_navbar(
                    project_path=arguments["project_path"],
                    app_name=arguments["app_name"],
                    schema=arguments["schema"],
                )
            # Scaffold tool
            elif name == "scaffold_frontend":
                return await client.scaffold_frontend(
                    project_path=arguments["project_path"],
                    app_name=arguments["app_name"],
                    schema=arguments["schema"],
                    api_url=arguments.get("api_url"),
                )
            # Utility tools
            elif name == "clone_template":
                return await client.clone_template(
                    destination=arguments["destination"],
                    project_name=arguments["project_name"],
                )
            elif name == "configure_api_url":
                return await client.configure_api_url(
                    project_path=arguments["project_path"],
                    api_url=arguments["api_url"],
                )
            elif name == "create_backend":
                return await client.create_backend(
                    name=arguments["name"],
                    schema=arguments["schema"],
                    description=arguments.get("description"),
                )
            elif name == "get_template_structure":
                return await client.get_template_structure(
                    path=arguments.get("path", ""),
                    max_depth=arguments.get("max_depth", 3),
                )
            else:
                raise ValueError(f"Unknown frontend tool: {name}")
    
    def _handle_scaffold_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        project_path = arguments.get("project_path", "") if arguments else ""
        app_name = arguments.get("app_name", "My App") if arguments else "My App"
        
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Scaffold frontend for "{app_name}" at {project_path}.

WORKFLOW:
1. Get the backend schema using get_schema (if you have project_id)
2. Or define a schema based on user requirements
3. Use scaffold_frontend with project_path, app_name, and schema
4. This will generate all types, API service, views, dashboard, routes, and navbar

The project should already exist (cloned from rationalbloksfront or equivalent).
Start now:""",
                    ),
                )
            ]
        )
    
    def _handle_fullstack_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
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

Use create_app tool with:
- name: {app_name}
- description: {description}
- destination: {destination}
- schema: Design based on description

Remember schema must be FLAT format. Start now:""",
                    ),
                )
            ]
        )


def create_frontend_server(
    api_key: str | None = None,
    http_mode: bool = False,
) -> FrontendMCPServer:
    """Factory function to create a frontend MCP server."""
    return FrontendMCPServer(api_key=api_key, http_mode=http_mode)
