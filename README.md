# RationalBloks MCP Server

**Unified MCP Server for RationalBloks** - Build fullstack applications with AI agents. Connect Claude Desktop, Cursor, VS Code Copilot, or any MCP-compatible client to create complete backends AND generate frontends.

[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/rationalbloks-mcp.svg)](https://pypi.org/project/rationalbloks-mcp/)

## 🚀 What's New in v0.3.2

**URL Fix** - Fixed API endpoint URL (was using wrong subdomain).

**Complete App Generation** - The `create_app` tool transforms a template into a fully working application in one step:

- **Full Mode**: All 24 tools (18 backend + 6 frontend) - DEFAULT
- **Backend Mode**: 18 API/database tools
- **Frontend Mode**: 6 frontend generation tools

**Key Feature**: `create_app` performs 13 automated steps including backend creation, TypeScript generation, API services, views, forms, dashboard, routing, and npm install - no manual steps required!

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

### Full Mode (Default) - 24 Tools

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

### Frontend Mode - 6 Tools

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

### Frontend Tools (6)

| Tool | Description |
|------|-------------|
| `create_app` | 🚀 **MAIN TOOL** - Create complete app in one step |
| `clone_template` | Clone rationalbloksfront template |
| `get_template_structure` | Explore template file structure |
| `read_template_file` | Read file from template |
| `create_backend` | Create backend via Backend MCP |
| `configure_api_url` | Set API URL in frontend .env |

## The `create_app` Tool

This is the primary tool that transforms a JSON schema into a complete working application:

### What It Does (13 Automated Steps)

1. **Clone Template** - Clone rationalbloksfront from GitHub
2. **Create Backend** - Create project via Backend MCP API
3. **Wait for Deployment** - Poll until staging is ready
4. **Generate Types** - Create TypeScript interfaces from schema
5. **Generate API Service** - Create typed HTTP client
6. **Generate Entity Views** - Create list/detail views for each entity
7. **Generate Forms** - Create add/edit forms with validation
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
│   ├── __init__.py      # Unified entry point (24 tools)
│   ├── core/            # Shared infrastructure
│   │   ├── auth.py      # API key validation
│   │   ├── transport.py # STDIO + HTTP transport
│   │   └── server.py    # Base MCP server
│   ├── backend/         # 18 backend tools
│   │   ├── client.py    # LogicBlok HTTP client
│   │   └── tools.py     # Tool definitions
│   └── frontend/        # 6 frontend tools
│       ├── client.py        # Template operations
│       ├── tools.py         # Tool definitions
│       └── app_generator.py # Complete app generation
├── pyproject.toml       # Package configuration
├── smithery.yaml        # Smithery marketplace config
└── README.md            # This file
```

## Version History

| Version | Date | Changes |
|---------|------|---------|| 0.3.2 | 2026-02-03 | Fixed API URL (businessblok → logicblok) || 0.3.1 | 2026-02-03 | Fixed wildcard handler lookup bug || 0.3.0 | 2026-02-03 | Added `create_app` tool for complete app generation |
| 0.2.2 | 2026-01-28 | Fixed frontend template URL |
| 0.2.0 | 2026-01-25 | Unified backend + frontend package |
| 0.1.0 | 2026-01-20 | Initial release (backend only) |

## Support

- **Email:** support@rationalbloks.com
- **Docs:** [rationalbloks.com/docs/mcp](https://rationalbloks.com/docs/mcp)
- **Issues:** [github.com/rationalbloks/rationalbloks-mcp/issues](https://github.com/rationalbloks/rationalbloks-mcp/issues)

## License

Proprietary - Copyright 2026 RationalBloks. All Rights Reserved.
