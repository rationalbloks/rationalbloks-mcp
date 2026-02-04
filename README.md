# RationalBloks MCP Server

**Unified MCP Server for RationalBloks** - Build fullstack applications with AI agents. Connect Claude Desktop, Cursor, VS Code Copilot, or any MCP-compatible client to create complete backends AND generate frontends.

[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/rationalbloks-mcp.svg)](https://pypi.org/project/rationalbloks-mcp/)

## 🚀 What's New in v0.4.5

**THE ONE WAY Architecture** - All generated code now uses our standardized npm packages:

- **@rationalbloks/frontblok-auth**: `createAuthApi` for authentication and token management
- **@rationalbloks/frontblok-crud**: `initApi` + `getApi` for generic CRUD operations

**Key Changes:**
- `generate_api_service` now generates THE ONE WAY pattern (no per-entity CRUD methods)
- All views use `getApi().getAll<T>(ENTITIES.X)` instead of `api.getTasks()`
- Forms use `getApi().create()` and `getApi().update()` for data operations
- ENTITIES constant provides type-safe entity name references
- Major simplification: ~50 lines per entity → ~40 lines TOTAL

**Previous in v0.4.1:**
- 14 granular frontend tools that work on ANY existing project
- `scaffold_frontend` - Apply all generators to your project (no cloning required)
- All file operations use `encoding="utf-8"` for Windows compatibility

## Installation

```bash
# Using uv (recommended)
uv pip install rationalbloks-mcp

# Using pip
pip install rationalbloks-mcp

# Using pipx (isolated environment)
pipx install rationalbloks-mcp
```

## Quick Start

### 1. Get Your API Key

1. Visit [rationalbloks.com/settings](https://rationalbloks.com/settings)
2. Create an API Key
3. Copy the key (format: `rb_sk_...`)

### 2. Configure Your AI Agent

#### VS Code / Cursor

Add to `settings.json`:

```json
{
  "mcp.servers": {
    "rationalbloks": {
      "command": "rationalbloks-mcp",
      "env": {
        "RATIONALBLOKS_API_KEY": "rb_sk_your_key_here",
        "RATIONALBLOKS_MODE": "full"
      }
    }
  }
}
```

**Reload window:** Ctrl+Shift+P → "Developer: Reload Window"

#### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rationalbloks": {
      "command": "rationalbloks-mcp",
      "env": {
        "RATIONALBLOKS_API_KEY": "rb_sk_your_key_here",
        "RATIONALBLOKS_MODE": "full"
      }
    }
  }
}
```

**Config location:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

#### Smithery (One-Click Install)

```bash
npx @smithery/cli install @rationalbloks/mcp
```

## Modes

### Full Mode (Default) - 32 Tools

All tools for complete fullstack development:

```bash
export RATIONALBLOKS_MODE=full
rationalbloks-mcp
# or just: rationalbloks-mcp (full is default)
```

### Backend Mode - 18 Tools

API and database operations only:

```bash
export RATIONALBLOKS_MODE=backend
rationalbloks-mcp
# or: rationalbloks-mcp-backend
```

### Frontend Mode - 14 Tools

Frontend generation only:

```bash
export RATIONALBLOKS_MODE=frontend
rationalbloks-mcp
# or: rationalbloks-mcp-frontend
```

## Available Tools

### Backend Tools (18)

**Read Operations (11):**
| Tool | Description |
|------|-------------|
| `list_projects` | List all projects |
| `get_project` | Get project details |
| `get_schema` | Get JSON schema |
| `get_user_info` | Get user information |
| `get_job_status` | Check deployment status |
| `get_project_info` | Detailed project info |
| `get_version_history` | Git commit history |
| `get_template_schemas` | Available templates ⭐ Start here! |
| `get_subscription_status` | Plan and limits |
| `get_project_usage` | Resource metrics |
| `get_schema_at_version` | Schema at specific commit |

**Write Operations (7):**
| Tool | Description |
|------|-------------|
| `create_project` | Create new project from schema |
| `update_schema` | Update project schema |
| `deploy_staging` | Deploy to staging |
| `deploy_production` | Deploy to production |
| `delete_project` | Delete project |
| `rollback_project` | Rollback to previous version |
| `rename_project` | Rename project |

### Frontend Tools (14)

**Generation Tools (8) - Work on ANY existing project:**
| Tool | Description |
|------|-------------|
| `generate_types` | Generate TypeScript interfaces from schema |
| `generate_api_service` | Generate API service using THE ONE WAY pattern |
| `generate_entity_view` | Generate list view using `getApi().getAll()` |
| `generate_entity_form` | Generate form using `getApi().create/update()` |
| `generate_all_views` | Generate all views for all entities |
| `generate_dashboard` | Generate dashboard with entity stats |
| `update_routes` | Add routes to App.tsx |
| `update_navbar` | Update navigation configuration |

**Scaffold Tools (2):**
| Tool | Description |
|------|-------------|
| `scaffold_frontend` | 🚀 **RECOMMENDED** - Apply ALL generators to existing project |
| `create_app` | Full automation (clone + backend + scaffold) |

**Utility Tools (4):**
| Tool | Description |
|------|-------------|
| `clone_template` | Clone rationalbloksfront template from GitHub |
| `configure_api_url` | Set API URL in frontend .env |
| `create_backend` | Create backend via Backend MCP |
| `get_template_structure` | Explore template file structure |

## Recommended Workflow

### If You Already Have a Project (Most Common)

Use `scaffold_frontend` - the RECOMMENDED approach for most use cases:

```
"Scaffold my frontend at ~/projects/my-app using this schema..."
```

This:
1. Generates TypeScript types
2. Creates API service using THE ONE WAY pattern
3. Generates list views for each entity (using `getApi().getAll()`)
4. Generates create/edit forms for each entity (using `getApi().create/update()`)
5. Creates a dashboard with entity stats
6. Updates App.tsx with routes
7. Updates Navbar with navigation
8. Optionally sets API URL in .env

**Benefits:** Works on ANY existing project. No cloning. No backend creation.

### If You Need a Fresh Template First

Use `clone_template`, then `scaffold_frontend`:

```
"Clone the template to ~/projects/my-app, then scaffold using this schema..."
```

### If You Want Everything Automated

Use `create_app` for the full automation flow (clone + backend + scaffold):

```
"Create a complete task manager app in ~/projects"
```

## THE ONE WAY Architecture

All generated frontend code uses our standardized npm packages for consistent, maintainable applications:

### Generated appApi.ts

```typescript
import { createAuthApi } from "@rationalbloks/frontblok-auth";
import { initApi, getApi } from "@rationalbloks/frontblok-crud";

const API_URL = import.meta.env.VITE_DATABASE_API_URL;

// Initialize auth API (handles tokens, login, logout)
const authApi = createAuthApi(API_URL);

// Initialize generic CRUD API (uses authApi for auth headers)
initApi(authApi);

// Type-safe entity constants
export const ENTITIES = {
  TASKS: "tasks",
  PROJECTS: "projects"
} as const;

export { authApi, getApi };
```

### Usage in Components

```typescript
import { getApi, ENTITIES } from "../../services/appApi";
import type { Task } from "../../types/generated";

// Fetch all
const tasks = await getApi().getAll<Task>(ENTITIES.TASKS);

// Fetch one
const task = await getApi().getOne<Task>(ENTITIES.TASKS, id);

// Create
await getApi().create<Task>(ENTITIES.TASKS, { title: "New Task" });

// Update
await getApi().update<Task>(ENTITIES.TASKS, id, { status: "done" });

// Delete
await getApi().remove(ENTITIES.TASKS, id);
```

### Benefits

- **Simplified Code**: No per-entity CRUD methods to generate
- **Type Safety**: ENTITIES constant provides type-safe entity names
- **Consistent Patterns**: Same API pattern across all components
- **Less Code**: ~40 lines total vs ~50 lines per entity
- **Easier Maintenance**: Changes to API behavior happen in npm packages

## The `create_app` Tool

This is the primary tool that transforms a JSON schema into a complete working application:

### What It Does (13 Automated Steps)

1. **Clone Template** - Clone rationalbloksfront from GitHub
2. **Create Backend** - Create project via Backend MCP API
3. **Wait for Deployment** - Poll until staging is ready
4. **Generate Types** - Create TypeScript interfaces from schema
5. **Generate API Service** - Create appApi.ts using THE ONE WAY pattern
6. **Generate Entity Views** - Create list views using `getApi().getAll()`
7. **Generate Forms** - Create add/edit forms using `getApi().create/update()`
8. **Generate Dashboard** - Create dashboard with entity cards
9. **Update Routes** - Configure React Router
10. **Update Navbar** - Add navigation links
11. **Cleanup** - Remove placeholder files
12. **Update package.json** - Set project name and description
13. **Install Dependencies** - Run `npm install`

### Usage

```
"Create a task manager app with projects and tasks in ~/projects"
```

The AI will:
1. Infer the schema (projects, tasks tables)
2. Call `create_app` with the schema
3. Return a complete working React app connected to a live REST API

### Input Schema

```json
{
  "name": "TaskManager",
  "description": "A task management application",
  "destination": "~/projects",
  "schema": {
    "projects": {
      "name": {"type": "string", "required": true},
      "description": {"type": "text"}
    },
    "tasks": {
      "title": {"type": "string", "required": true},
      "status": {"type": "string", "enum": ["todo", "in_progress", "done"]},
      "project_id": {"type": "uuid", "foreign_key": "projects.id"}
    }
  }
}
```

## Schema Format

⚠️ **CRITICAL: Use FLAT format (no 'fields' nesting)**

✅ **Correct:**
```json
{
  "users": {
    "email": {"type": "string", "required": true, "unique": true},
    "name": {"type": "string", "required": true}
  },
  "posts": {
    "title": {"type": "string", "required": true},
    "user_id": {"type": "uuid", "foreign_key": "users.id"}
  }
}
```

❌ **Wrong (will fail):**
```json
{
  "users": {
    "fields": {
      "email": {"type": "string"}
    }
  }
}
```

### Field Types

| Type | Description |
|------|-------------|
| `string` | Text (varchar) |
| `text` | Long text |
| `integer` | Whole numbers |
| `decimal` | Decimal numbers |
| `boolean` | True/false |
| `uuid` | Primary/foreign keys |
| `date` | Date only |
| `timestamp` | Date and time |
| `json` | JSON data |

### Field Properties

| Property | Type | Description |
|----------|------|-------------|
| `type` | string | **REQUIRED** - Field type |
| `required` | boolean | Field is required |
| `unique` | boolean | Unique constraint |
| `default` | any | Default value |
| `foreign_key` | string | Reference (format: `table.id`) |
| `enum` | array | Allowed values |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RATIONALBLOKS_API_KEY` | Your API key | Required for STDIO |
| `RATIONALBLOKS_MODE` | Mode: full, backend, frontend | `full` |
| `RATIONALBLOKS_BASE_URL` | API Gateway URL | `https://businessblok.rationalbloks.com` |
| `RATIONALBLOKS_TIMEOUT` | Request timeout (seconds) | `30` |
| `RATIONALBLOKS_LOG_LEVEL` | Logging level | `INFO` |
| `TRANSPORT` | Transport: stdio, http | `stdio` |

## Entry Points

Three entry points for different use cases:

```bash
# Full mode (all 24 tools)
rationalbloks-mcp

# Backend only (18 tools)
rationalbloks-mcp-backend

# Frontend only (6 tools)
rationalbloks-mcp-frontend
```

## Example Prompts

### Quick Start (Recommended)

> "Create a todo app with projects and tasks in ~/projects"

This single prompt will create a complete working application!

### Backend Operations

> "List all my RationalBloks projects"

> "Create a project called 'e-commerce' with products, orders, and customers"

> "Deploy my project to staging"

> "Show me the deployment history"

> "Get me some template schemas to start with"

### Frontend Operations

> "Clone the frontend template to ~/projects/my-store"

> "What files are in the template?"

> "Connect my-store to the e-commerce backend"

### Fullstack (Full Mode)

> "Create a complete inventory management system with products, categories, and suppliers"

> "Build me an e-commerce store with product catalog and shopping cart"

> "Create a CRM with customers, contacts, and deals"

## Troubleshooting

### "Command not found"
```bash
pip show rationalbloks-mcp
which rationalbloks-mcp  # Unix
where rationalbloks-mcp  # Windows
```

### "API key required"
Ensure your key starts with `rb_sk_`

### Tools not loading
1. Check IDE Output panel for errors
2. Reload window (Ctrl+Shift+P → "Developer: Reload Window")
3. Verify settings.json syntax

### Schema errors
1. Use `get_template_schemas` to see correct format
2. Ensure FLAT format (no 'fields' nesting)
3. Every field needs a 'type' property

### Deployment stuck
1. Use `get_job_status` to check deployment status
2. Use `get_project_info` for detailed pod status
3. Common cause: schema format error (nested 'fields' key)

## Architecture

```
rationalbloks-mcp/
├── src/rationalbloks_mcp/
│   ├── __init__.py      # Unified entry point (32 tools)
│   ├── core/            # Shared infrastructure
│   │   ├── auth.py      # API key validation
│   │   ├── transport.py # STDIO + HTTP transport
│   │   └── server.py    # Base MCP server
│   ├── backend/         # 18 backend tools
│   │   ├── client.py    # LogicBlok HTTP client
│   │   └── tools.py     # Tool definitions
│   └── frontend/        # 14 frontend tools
│       ├── client.py        # Generation methods
│       ├── tools.py         # Tool definitions
│       └── app_generator.py # Full app automation
├── pyproject.toml       # Package configuration
├── smithery.yaml        # Smithery marketplace config
└── README.md            # This file
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.4.1 | 2026-02-03 | Major redesign: 14 granular frontend tools, scaffold_frontend |
| 0.3.5 | 2026-02-03 | Fixed encoding for Windows (utf-8) |
| 0.3.4 | 2026-02-03 | Fixed client to use /api/mcp/execute gateway pattern |
| 0.3.3 | 2026-02-03 | Added certifi for SSL cert resolution |
| 0.3.2 | 2026-02-03 | Fixed API URL (businessblok → logicblok) |
| 0.3.1 | 2026-02-03 | Fixed wildcard handler lookup bug |
| 0.3.0 | 2026-02-03 | Added create_app tool for complete app generation |
| 0.2.2 | 2026-01-28 | Fixed frontend template URL |
| 0.2.0 | 2026-01-25 | Unified backend + frontend package |
| 0.1.0 | 2026-01-20 | Initial release (backend only) |

## Support

- **Email:** support@rationalbloks.com
- **Docs:** [rationalbloks.com/docs/mcp](https://rationalbloks.com/docs/mcp)
- **Issues:** [github.com/rationalbloks/rationalbloks-mcp/issues](https://github.com/rationalbloks/rationalbloks-mcp/issues)

## License

Proprietary - Copyright 2026 RationalBloks. All Rights Reserved.
