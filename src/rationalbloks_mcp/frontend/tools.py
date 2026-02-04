# ============================================================================
# RATIONALBLOKS MCP - FRONTEND TOOLS (THIN LAYER)
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# THE PHILOSOPHY:
# This MCP is a THIN LAYER that provides guardrails, not generation.
# The AI agent (Claude) does the creative work. The MCP ensures the AI
# follows THE ONE WAY architecture using frontblok-auth + frontblok-crud.
#
# WHAT THE MCP DOES:
#   1. BOOTSTRAP: Clone template, generate types, generate datablokApi.ts
#   2. TEACH: Provide architecture docs and guidelines
#   3. VALIDATE: Ensure components follow THE ONE WAY pattern
#
# WHAT THE AI DOES:
#   1. Design appropriate UI for each entity (kanban, calendar, cards, etc.)
#   2. Write React components that follow the patterns
#   3. Create custom layouts and interactions
#
# THE ONE WAY ARCHITECTURE:
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  @rationalbloks/frontblok-auth  →  createAuthApi, auth context          │
# │  @rationalbloks/frontblok-crud  →  initApi, getApi for all CRUD         │
# │  datablokApi.ts                 →  THE ONE WAY glue file                │
# └─────────────────────────────────────────────────────────────────────────┘
#
# 6 TOOLS ONLY:
#   📖 TEACH:
#     - get_frontend_guidelines: THE ONE WAY architecture + coding rules
#     - get_template_structure: Explore rationalbloksfront template
#
#   🔧 BOOTSTRAP (one-time setup):
#     - clone_template: Fresh project from GitHub
#     - generate_types: TypeScript interfaces from schema
#     - generate_api_service: datablokApi.ts (THE ONE WAY glue)
#     - configure_api_url: Set .env API URL
#
# ============================================================================

from typing import Any

from mcp.types import Prompt, PromptArgument, PromptMessage, GetPromptResult, TextContent

from .. import __version__
from ..core import BaseMCPServer
from .client import FrontendClient

# Public API
__all__ = [
    "FRONTEND_TOOLS",
    "FrontendMCPServer",
    "create_frontend_server",
]


# ============================================================================
# THE ONE WAY ARCHITECTURE DOCUMENTATION
# ============================================================================

THE_ONE_WAY_ARCHITECTURE = """
# THE ONE WAY - RationalBloks Frontend Architecture

## Overview

Every RationalBloks frontend follows THE ONE WAY pattern:
- **frontblok-auth**: Authentication, tokens, user context
- **frontblok-crud**: Generic CRUD operations via getApi()
- **datablokApi.ts**: The glue file that wires them together

## The Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         YOUR COMPONENTS                                      │
│                                                                              │
│   import { getApi, ENTITIES, useClientAuth } from '../services/datablokApi' │
│   const items = await getApi().getAll<Item>(ENTITIES.ITEMS)                 │
│   const { user, isAuthenticated, logout } = useClientAuth()                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────┬──────────┘
                                                                   │
                                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         datablokApi.ts (THE GLUE)                           │
│                                                                              │
│   import { createAuthApi, createAuthProvider, useAuth } from 'frontblok-auth'│
│   import { initApi, getApi } from 'frontblok-crud'                          │
│                                                                              │
│   export const authApi = createAuthApi(API_URL)                             │
│   initApi(authApi)  // Wire CRUD to use auth's HTTP layer                   │
│                                                                              │
│   export const ENTITIES = { TASKS: 'tasks', ... } as const                  │
│   export const ClientAuthProvider = createAuthProvider(authApi)             │
│   export const useClientAuth = useAuth                                      │
│   export { getApi }                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                       ┌───────────────┴───────────────┐
                       ▼                               ▼
┌─────────────────────────────────────┐ ┌─────────────────────────────────────┐
│      @rationalbloks/frontblok-auth  │ │      @rationalbloks/frontblok-crud  │
│                                     │ │                                     │
│   createAuthApi(url)                │ │   initApi(authApi)                  │
│   createAuthProvider(authApi)       │ │   getApi()                          │
│   useAuth()                         │ │     .getAll<T>(entity)              │
│   createAppRoot(App, config)        │ │     .getOne<T>(entity, id)          │
│                                     │ │     .create<T>(entity, data)        │
│                                     │ │     .update<T>(entity, id, data)    │
│                                     │ │     .remove(entity, id)             │
└─────────────────────────────────────┘ └─────────────────────────────────────┘
```

## Provider Hierarchy in App.tsx

```tsx
<ErrorBoundary>
  <QueryClientProvider client={queryClient}>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <ClientAuthProvider>
          <AppRouter />
        </ClientAuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  </QueryClientProvider>
</ErrorBoundary>
```

## CRUD Operations (THE ONE WAY)

```tsx
import { getApi, ENTITIES } from '../services/datablokApi';
import type { Task, CreateTaskInput } from '../types/generated';

// READ all
const tasks = await getApi().getAll<Task>(ENTITIES.TASKS);

// READ one
const task = await getApi().getOne<Task>(ENTITIES.TASKS, id);

// CREATE
const newTask = await getApi().create<Task>(ENTITIES.TASKS, { title: 'New' });

// UPDATE
const updated = await getApi().update<Task>(ENTITIES.TASKS, id, { title: 'Updated' });

// DELETE
await getApi().remove(ENTITIES.TASKS, id);

// QUERY with filters
const filtered = await getApi().getAll<Task>(ENTITIES.TASKS, {
  status: 'active',
  limit: 10,
  order_by: 'created_at',
  order_dir: 'desc'
});
```

## Authentication (via useClientAuth)

```tsx
import { useClientAuth } from '../services/datablokApi';

function MyComponent() {
  const { 
    user,           // Current user or null
    isAuthenticated,// Boolean
    isLoading,      // Loading state
    login,          // (email, password) => Promise
    register,       // (email, password, name?, company?) => Promise
    logout,         // () => void
    error           // Error message or null
  } = useClientAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/auth" />;
  }
  
  return <div>Welcome, {user?.name}</div>;
}
```

## File Structure

```
src/
├── services/
│   └── datablokApi.ts       ← THE ONE WAY glue (generated by MCP)
├── types/
│   └── generated.ts         ← TypeScript types (generated by MCP)
├── components/
│   ├── shared/              ← Reusable UI components
│   │   ├── Navbar.tsx       ← Factory: createNavbar(config)
│   │   ├── ErrorBoundary.tsx
│   │   └── ...
│   └── views/               ← Page components (YOU write these)
│       ├── DashboardView.tsx
│       ├── TasksView.tsx     ← Your custom UI (kanban, calendar, etc.)
│       └── ...
├── config/
│   └── Navbar.tsx           ← createNavbar() with your nav items
├── theme/
│   └── index.ts             ← createAppTheme()
├── App.tsx                  ← Provider hierarchy + routes
└── main.tsx                 ← createAppRoot(App, config)
```

## Key Rules

1. **NEVER create API clients manually** - use getApi() from datablokApi
2. **NEVER manage auth state manually** - use useClientAuth()
3. **ALWAYS import from datablokApi** - it's the single source of truth
4. **ALWAYS use ENTITIES constant** - type-safe entity names
5. **ALWAYS use generated types** - from types/generated.ts
"""

COMPONENT_GUIDELINES = """
# Component Development Guidelines

## View Component Pattern

Every view component should follow this structure:

```tsx
// src/components/views/{Entity}View.tsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Button, CircularProgress, Alert } from '@mui/material';
import { getApi, ENTITIES } from '../../services/datablokApi';
import type { Entity } from '../../types/generated';

export default function EntityView() {
  const navigate = useNavigate();
  const [items, setItems] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await getApi().getAll<Entity>(ENTITIES.ENTITY_NAME);
      setItems(data);
      setError(null);
    } catch (err) {
      setError('Failed to load data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this item?')) return;
    try {
      await getApi().remove(ENTITIES.ENTITY_NAME, id);
      setItems(items.filter(item => item.id !== id));
    } catch (err) {
      setError('Failed to delete');
    }
  };

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <Box>
      <Typography variant="h4">Entity List</Typography>
      <Button onClick={() => navigate('/entity/new')}>Add New</Button>
      {/* YOUR CUSTOM UI HERE - tables, cards, kanban, calendar, etc. */}
    </Box>
  );
}
```

## Form Component Pattern

```tsx
// src/components/views/{Entity}FormView.tsx
import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Box, TextField, Button, CircularProgress, Alert } from '@mui/material';
import { getApi, ENTITIES } from '../../services/datablokApi';
import type { Entity, CreateEntityInput } from '../../types/generated';

export default function EntityFormView() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditMode = Boolean(id);
  
  const [formData, setFormData] = useState<Partial<CreateEntityInput>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isEditMode && id) {
      loadEntity(id);
    }
  }, [id]);

  const loadEntity = async (entityId: string) => {
    try {
      setLoading(true);
      const data = await getApi().getOne<Entity>(ENTITIES.ENTITY_NAME, entityId);
      setFormData(data);
    } catch (err) {
      setError('Failed to load entity');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      if (isEditMode && id) {
        await getApi().update<Entity>(ENTITIES.ENTITY_NAME, id, formData);
      } else {
        await getApi().create<Entity>(ENTITIES.ENTITY_NAME, formData as CreateEntityInput);
      }
      navigate('/entity');
    } catch (err) {
      setError('Failed to save');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit}>
      <Typography variant="h4">{isEditMode ? 'Edit' : 'Create'} Entity</Typography>
      {/* YOUR FORM FIELDS HERE */}
      <Button type="submit" disabled={loading}>Save</Button>
    </Box>
  );
}
```

## Navbar Configuration (Factory Pattern)

```tsx
// src/config/Navbar.tsx
import { Dashboard, List } from '@mui/icons-material';
import { createNavbar, NavigationItem } from '../components/shared/Navbar';
import { useClientAuth } from '../services/datablokApi';

const BRAND_CONFIG = {
  name: 'My App',
  logo: '/favicon.ico',
};

const PUBLIC_NAV_ITEMS: NavigationItem[] = [
  { id: '/', label: 'Home', icon: <Dashboard /> },
];

const AUTHENTICATED_NAV_ITEMS: NavigationItem[] = [
  { id: '/dashboard', label: 'Dashboard', icon: <Dashboard /> },
  { id: '/tasks', label: 'Tasks', icon: <List /> },
  // Add your entities here
];

const Navbar = createNavbar({
  brand: BRAND_CONFIG,
  navigation: {
    public: PUBLIC_NAV_ITEMS,
    authenticated: AUTHENTICATED_NAV_ITEMS,
  },
  useAuth: useClientAuth,
  userRoleLabel: 'User',
  authRoute: '/auth',
  settingsRoute: '/settings',
});

export default Navbar;
```

## Theme Customization

```tsx
// src/theme/index.ts
import { createTheme } from '@mui/material/styles';

export const createAppTheme = () => createTheme({
  palette: {
    primary: { main: '#1976d2' },
    secondary: { main: '#dc004e' },
    background: { default: '#f5f5f5' },
  },
  // Customize typography, components, etc.
});
```

## Choosing the Right UI

Based on the entity semantics, choose appropriate UI:

| Entity Type | Recommended UI |
|-------------|----------------|
| Tasks/Issues | Kanban board with status columns |
| Events/Schedules | Calendar view |
| Products/Items | Card grid with images |
| Users/Profiles | Profile cards or table |
| Logs/History | Timeline or table |
| Inventory | Table with stock indicators |
| Locations | Map view or card grid |

## MUI Components Available

The template includes Material-UI. Use these components:
- Layout: Box, Container, Grid, Stack
- Surfaces: Card, Paper, Accordion
- Data Display: Table, List, Typography, Chip, Avatar
- Inputs: TextField, Select, Checkbox, DatePicker
- Feedback: Alert, Snackbar, CircularProgress, Skeleton
- Navigation: Tabs, Breadcrumbs, Menu

## Important: DO NOT

1. ❌ Create new API service files - use datablokApi
2. ❌ Implement manual token handling - frontblok-auth handles it
3. ❌ Use fetch/axios directly - use getApi()
4. ❌ Create custom auth contexts - use ClientAuthProvider
5. ❌ Define entity names as strings - use ENTITIES constant
"""


# ============================================================================
# TOOL DEFINITIONS (6 TOOLS ONLY)
# ============================================================================

FRONTEND_TOOLS = [
    # ========================================================================
    # 📖 TEACH TOOLS - Provide guidelines to AI
    # ========================================================================
    {
        "name": "get_frontend_guidelines",
        "title": "Get Frontend Guidelines",
        "description": """Get THE ONE WAY architecture documentation and coding guidelines.

Returns comprehensive documentation for building RationalBloks frontends:
- THE ONE WAY architecture explanation
- How to use frontblok-auth and frontblok-crud
- Component patterns (views, forms, navbar)
- CRUD operation examples
- Authentication patterns
- File structure
- Key rules to follow

USE THIS FIRST when building a frontend. Read and follow these guidelines.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "section": {
                    "type": "string",
                    "enum": ["architecture", "components", "all"],
                    "description": "Which section to return (default: all)"
                }
            },
            "required": []
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_template_structure",
        "title": "Get Template Structure",
        "description": """Get the file structure of the rationalbloksfront template.

Returns a tree view of key directories and files, showing:
- Where to put your components
- Existing patterns to follow
- Configuration files
- Shared components available

Use this to understand the template before writing code.""",
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
    # ========================================================================
    # 🔧 BOOTSTRAP TOOLS - One-time setup
    # ========================================================================
    {
        "name": "clone_template",
        "title": "Clone Template",
        "description": """Clone the rationalbloksfront template from GitHub.

Creates a fresh project with:
- React + Vite + TypeScript setup
- @rationalbloks/frontblok-auth installed
- @rationalbloks/frontblok-crud installed
- MUI (Material-UI) components
- Template views and shared components
- Proper project structure

WORKFLOW:
1. clone_template → Fresh project
2. generate_types → TypeScript interfaces from your schema
3. generate_api_service → datablokApi.ts with ENTITIES
4. configure_api_url → Set backend URL
5. Write your custom views (AI creativity)""",
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
        "name": "generate_types",
        "title": "Generate TypeScript Types",
        "description": """Generate TypeScript interfaces from a database schema.

Creates src/types/generated.ts with:
- Interface for each entity (Task, Project, etc.)
- CreateInput types for forms (CreateTaskInput)
- UpdateInput types (Partial of CreateInput)
- Proper type mapping from schema types

EXAMPLE OUTPUT:
```typescript
export interface Task {
  id: string;
  title: string;
  status?: 'pending' | 'in_progress' | 'completed';
  due_date?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTaskInput {
  title: string;
  status?: 'pending' | 'in_progress' | 'completed';
  due_date?: string;
}

export type UpdateTaskInput = Partial<CreateTaskInput>;
```

Run this after clone_template, before writing components.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Absolute path to your frontend project"
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
        "description": """Generate datablokApi.ts - THE ONE WAY glue file.

Creates src/services/datablokApi.ts with:
- Import from @rationalbloks/frontblok-auth
- Import from @rationalbloks/frontblok-crud  
- authApi singleton (createAuthApi)
- initApi() call to wire CRUD to auth
- ENTITIES constant with all table names
- ClientAuthProvider and useClientAuth exports
- getApi export for CRUD operations

THIS IS THE ONLY API FILE YOU NEED. All components import from here.

EXAMPLE OUTPUT:
```typescript
import { createAuthApi, createAuthProvider, useAuth } from '@rationalbloks/frontblok-auth';
import { initApi, getApi } from '@rationalbloks/frontblok-crud';

const API_URL = import.meta.env.VITE_DATABASE_API_URL;
export const authApi = createAuthApi(API_URL);
initApi(authApi);

export const ENTITIES = {
  TASKS: 'tasks',
  PROJECTS: 'projects',
} as const;

export const ClientAuthProvider = createAuthProvider(authApi);
export const useClientAuth = useAuth;
export { getApi };
```

Run this after generate_types.""",
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
                    "description": "Backend API URL (optional - uses env var if not provided)"
                }
            },
            "required": ["project_path", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "configure_api_url",
        "title": "Configure API URL",
        "description": """Set the backend API URL in .env file.

Updates VITE_DATABASE_API_URL to point to your RationalBloks backend.
Creates .env from .env.example if needed.

Run this after generate_api_service.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_path": {
                    "type": "string",
                    "description": "Path to the frontend project"
                },
                "api_url": {
                    "type": "string",
                    "description": "Backend API URL (e.g., https://my-app-staging.rationalbloks.com)"
                }
            },
            "required": ["project_path", "api_url"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False}
    },
]


# ============================================================================
# FRONTEND PROMPTS
# ============================================================================

FRONTEND_PROMPTS = [
    Prompt(
        name="build-frontend",
        title="Build Frontend from Schema",
        description="Build a custom frontend for a RationalBloks backend",
        arguments=[
            PromptArgument(
                name="project_path",
                description="Path where the project should be created or exists",
                required=True,
            ),
            PromptArgument(
                name="app_name",
                description="Display name for your app",
                required=True,
            ),
            PromptArgument(
                name="app_description",
                description="What the app should do and look like",
                required=True,
            ),
        ],
    ),
]


# ============================================================================
# FRONTEND MCP SERVER
# ============================================================================

class FrontendMCPServer(BaseMCPServer):
    """Frontend MCP server - THIN LAYER for guardrails, not generation.
    
    6 tools only:
    - get_frontend_guidelines: THE ONE WAY architecture docs
    - get_template_structure: Explore template
    - clone_template: Fresh project from GitHub
    - generate_types: TypeScript from schema
    - generate_api_service: datablokApi.ts (THE ONE WAY glue)
    - configure_api_url: Set .env
    
    The AI agent writes all views, forms, and custom UI.
    """
    
    INSTRUCTIONS = """RationalBloks Frontend MCP - THIN LAYER

This MCP provides guardrails, not generation. YOU (the AI agent) write the components.

## 📖 LEARN FIRST
- get_frontend_guidelines: Read THE ONE WAY architecture
- get_template_structure: See what's in the template

## 🔧 BOOTSTRAP (one-time setup)
1. clone_template: Get fresh project
2. generate_types: TypeScript interfaces from schema  
3. generate_api_service: Create datablokApi.ts
4. configure_api_url: Set backend URL

## ✨ THEN YOU (AI) CREATE
- Custom views for each entity (kanban, calendar, cards, tables)
- Forms with appropriate inputs
- Dashboard with meaningful stats
- Routes in App.tsx
- Navbar configuration

## KEY RULES
- All imports from '../services/datablokApi'
- Use getApi() for CRUD, useClientAuth() for auth
- Use ENTITIES constant for type-safe entity names
- Use types from '../types/generated'

Read get_frontend_guidelines first to understand the patterns!"""
    
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
        self.register_prompt_handler("build-frontend", self._handle_build_prompt)
        self.setup_handlers()
    
    def _get_client(self) -> FrontendClient:
        api_key = self.get_api_key_for_request()
        return FrontendClient(api_key)
    
    async def _handle_frontend_tool(self, name: str, arguments: dict) -> Any:
        """Handle all frontend tool calls."""
        
        # TEACH tools - return documentation
        if name == "get_frontend_guidelines":
            section = arguments.get("section", "all")
            if section == "architecture":
                return {"guidelines": THE_ONE_WAY_ARCHITECTURE}
            elif section == "components":
                return {"guidelines": COMPONENT_GUIDELINES}
            else:
                return {
                    "guidelines": THE_ONE_WAY_ARCHITECTURE + "\n\n---\n\n" + COMPONENT_GUIDELINES
                }
        
        # All other tools use FrontendClient
        async with self._get_client() as client:
            if name == "get_template_structure":
                return await client.get_template_structure(
                    path=arguments.get("path", ""),
                    max_depth=arguments.get("max_depth", 3),
                )
            elif name == "clone_template":
                return await client.clone_template(
                    destination=arguments["destination"],
                    project_name=arguments["project_name"],
                )
            elif name == "generate_types":
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
            elif name == "configure_api_url":
                return await client.configure_api_url(
                    project_path=arguments["project_path"],
                    api_url=arguments["api_url"],
                )
            else:
                raise ValueError(f"Unknown frontend tool: {name}")
    
    def _handle_build_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        project_path = arguments.get("project_path", "") if arguments else ""
        app_name = arguments.get("app_name", "My App") if arguments else "My App"
        app_description = arguments.get("app_description", "") if arguments else ""
        
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Build a frontend for "{app_name}" at {project_path}.

App Description: {app_description}

WORKFLOW:
1. Read get_frontend_guidelines to understand THE ONE WAY architecture
2. Use clone_template if you need a fresh project
3. Get the schema from the backend (use backend MCP get_schema if available)
4. Use generate_types to create TypeScript interfaces
5. Use generate_api_service to create datablokApi.ts
6. Use configure_api_url to set the backend URL
7. NOW YOU WRITE THE COMPONENTS:
   - Design appropriate UI for each entity (not just tables!)
   - Consider: kanban, calendar, cards, maps based on entity type
   - Write views, forms, update routes, update navbar
8. Run npm install && npm run dev to test

Remember: The MCP does bootstrap only. You design the UI!

Start now:""",
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
