# RationalBloks MCP Server

**The AI-First Backend Platform** - Deploy production APIs in minutes, let AI agents build your frontend.

[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/rationalbloks-mcp.svg)](https://pypi.org/project/rationalbloks-mcp/)

## 🚀 What's New in v0.5.0

**THIN FRONTEND MCP** - The frontend MCP is now a thin layer that provides guardrails, not generation. The AI agent writes all views, forms, and custom UI.

**Philosophy Change:**
- **Backend MCP (18 tools)**: Deterministic, reliable infrastructure operations
- **Frontend MCP (6 tools)**: Bootstrap only - clone, types, API glue, config
- **AI Agent**: Creative work - writes custom views (kanban, calendar, cards - not boring tables!)

**THE ONE WAY Architecture:**
- `@rationalbloks/frontblok-auth`: Authentication and token management
- `@rationalbloks/frontblok-crud`: Generic CRUD via `getApi()`
- `datablokApi.ts`: The glue file that wires them together

---

## Installation

```bash
# Using pip
pip install rationalbloks-mcp

# Using uv (recommended)
uv pip install rationalbloks-mcp

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
        "RATIONALBLOKS_API_KEY": "rb_sk_your_key_here"
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
        "RATIONALBLOKS_API_KEY": "rb_sk_your_key_here"
      }
    }
  }
}
```

**Config location:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

---

## Modes

| Mode | Tools | Use Case |
|------|-------|----------|
| **full** (default) | 24 | Complete fullstack development |
| **backend** | 18 | API/database operations only |
| **frontend** | 6 | Frontend bootstrap only |

```bash
# Full mode (default)
rationalbloks-mcp

# Backend only
RATIONALBLOKS_MODE=backend rationalbloks-mcp

# Frontend only  
RATIONALBLOKS_MODE=frontend rationalbloks-mcp
```

---

## Backend MCP (18 Tools)

The backend MCP provides deterministic, reliable infrastructure operations.

### Read Operations (11 tools)

| Tool | Description |
|------|-------------|
| `list_projects` | List all your projects |
| `get_project` | Get project details |
| `get_schema` | Get current JSON schema |
| `get_user_info` | Get authenticated user info |
| `get_job_status` | Check deployment job status |
| `get_project_info` | Detailed project info with K8s status |
| `get_version_history` | Git commit history |
| `get_template_schemas` | ⭐ Pre-built schema templates |
| `get_subscription_status` | Plan and usage limits |
| `get_project_usage` | CPU/memory metrics |
| `get_schema_at_version` | Schema at specific commit |

### Write Operations (7 tools)

| Tool | Description |
|------|-------------|
| `create_project` | Create new project from schema |
| `update_schema` | Update project schema |
| `deploy_staging` | Deploy to staging environment |
| `deploy_production` | Deploy to production |
| `delete_project` | Delete project permanently |
| `rollback_project` | Rollback to previous version |
| `rename_project` | Rename project |

### Schema Format (CRITICAL)

```json
// ✅ CORRECT - FLAT format
{
  "tasks": {
    "title": {"type": "string", "max_length": 200, "required": true},
    "status": {"type": "string", "max_length": 50, "enum": ["pending", "done"]}
  }
}

// ❌ WRONG - nested 'fields' key
{
  "tasks": {
    "fields": {
      "title": {"type": "string"}
    }
  }
}
```

### Field Types

| Type | Required Properties |
|------|---------------------|
| `string` | `max_length` (e.g., 255) |
| `text` | None |
| `integer` | None |
| `decimal` | `precision`, `scale` |
| `boolean` | None |
| `uuid` | None |
| `date` | None |
| `datetime` | None |
| `json` | None |

### Auto-Generated Fields

Don't define these - they're automatic:
- `id` (UUID primary key)
- `created_at` (datetime)
- `updated_at` (datetime)

### User Authentication

**NEVER create users/customers/employees tables with email/password.** Use the built-in `app_users` table:

```json
{
  "employee_profiles": {
    "user_id": {"type": "uuid", "foreign_key": "app_users.id", "required": true},
    "department": {"type": "string", "max_length": 100}
  }
}
```

---

## Frontend MCP (6 Tools)

The frontend MCP is a **THIN LAYER** that provides guardrails, not generation. The AI agent writes all views, forms, and custom UI.

### 📖 TEACH Tools (2)

| Tool | Description |
|------|-------------|
| `get_frontend_guidelines` | THE ONE WAY architecture documentation |
| `get_template_structure` | Explore rationalbloksfront template files |

### 🔧 BOOTSTRAP Tools (4)

| Tool | Description |
|------|-------------|
| `clone_template` | Clone rationalbloksfront from GitHub |
| `generate_types` | Generate TypeScript interfaces from schema |
| `generate_api_service` | Generate `datablokApi.ts` (THE ONE WAY glue) |
| `configure_api_url` | Set `VITE_DATABASE_API_URL` in `.env` |

### The Philosophy

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP (THIN LAYER)                             │
│                                                                 │
│  📖 TEACH: get_frontend_guidelines, get_template_structure      │
│  🔧 BOOTSTRAP: clone_template, generate_types,                  │
│                generate_api_service, configure_api_url          │
│                                                                 │
│  That's it. The MCP provides guardrails, not generation.        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI AGENT (Creative Work)                      │
│                                                                 │
│  ✨ Write custom views (kanban, calendar, cards, maps)          │
│  ✨ Design forms with appropriate inputs                        │
│  ✨ Create meaningful dashboards                                │
│  ✨ Set up routes and navbar                                    │
│  ✨ Make it beautiful and domain-specific                       │
│                                                                 │
│  Following THE ONE WAY: all imports from datablokApi.ts         │
└─────────────────────────────────────────────────────────────────┘
```

---

## THE ONE WAY Architecture

All frontend code follows this pattern:

### datablokApi.ts (Generated by MCP)

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

### Usage in Components (Written by AI)

```typescript
import { getApi, ENTITIES, useClientAuth } from '../services/datablokApi';
import type { Task } from '../types/generated';

// CRUD operations
const tasks = await getApi().getAll<Task>(ENTITIES.TASKS);
const task = await getApi().getOne<Task>(ENTITIES.TASKS, id);
await getApi().create<Task>(ENTITIES.TASKS, { title: 'New Task' });
await getApi().update<Task>(ENTITIES.TASKS, id, { title: 'Updated' });
await getApi().remove(ENTITIES.TASKS, id);

// Authentication
const { user, isAuthenticated, login, logout } = useClientAuth();
```

---

## Recommended Workflow

### Step 1: Create Backend

```
"Create a task management API with tasks, projects, and comments"
```

The AI agent will:
1. Design the schema following the rules
2. Use `create_project` to deploy the backend
3. Wait for deployment with `get_job_status`

### Step 2: Bootstrap Frontend

```
"Clone the template and set up the frontend for my task manager"
```

The AI agent will:
1. Read `get_frontend_guidelines` to understand THE ONE WAY
2. Use `clone_template` to get fresh project
3. Use `generate_types` to create TypeScript interfaces
4. Use `generate_api_service` to create `datablokApi.ts`
5. Use `configure_api_url` to set the backend URL

### Step 3: AI Writes Custom Views

```
"Create a kanban board view for tasks with drag-and-drop between status columns"
```

The AI agent will:
1. Write `TasksView.tsx` with kanban UI
2. Use `getApi().getAll()` and `getApi().update()` for data
3. Import types from `../types/generated`
4. Follow the patterns from `get_frontend_guidelines`

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RATIONALBLOKS_API_KEY` | Your API key (required) | - |
| `RATIONALBLOKS_MODE` | Mode: full, backend, frontend | `full` |
| `RATIONALBLOKS_BASE_URL` | API Gateway URL | `https://businessblok.rationalbloks.com` |
| `RATIONALBLOKS_TIMEOUT` | Request timeout (seconds) | `30` |
| `RATIONALBLOKS_LOG_LEVEL` | Log level | `INFO` |

---

## NPM Packages

The generated frontend uses these npm packages:

| Package | Purpose |
|---------|---------|
| `@rationalbloks/frontblok-auth` | Authentication, tokens, user context |
| `@rationalbloks/frontblok-crud` | Generic CRUD via `getApi()` |

Install in your project:

```bash
npm install @rationalbloks/frontblok-auth @rationalbloks/frontblok-crud
```

---

## Support

- **Documentation:** [rationalbloks.com/docs](https://rationalbloks.com/docs)
- **Issues:** [github.com/rationalbloks/rationalbloks-mcp/issues](https://github.com/rationalbloks/rationalbloks-mcp/issues)
- **Email:** support@rationalbloks.com

---

## License

Proprietary - Copyright 2026 RationalBloks. All Rights Reserved.

See [LICENSE](LICENSE) for details.
