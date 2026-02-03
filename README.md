# RationalBloks MCP Server

**Unified MCP Server for RationalBloks** - Build fullstack applications with AI agents. Connect Claude Desktop, Cursor, VS Code Copilot to manage backends AND generate frontends.

[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/rationalbloks-mcp.svg)](https://pypi.org/project/rationalbloks-mcp/)

## 🚀 What's New in v0.2.2

**Unified Package** - Single package with 3 modes:
- **full**: All 23 tools (backend + frontend) - DEFAULT
- **backend**: 18 API/database tools
- **frontend**: 5 frontend generation tools

## Installation

```bash
# Using uv (recommended)
uv pip install rationalbloks-mcp

# Using pip
pip install rationalbloks-mcp
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

## Modes

### Full Mode (Default) - 23 Tools

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

### Frontend Mode - 5 Tools

Frontend generation only:

```bash
export RATIONALBLOKS_MODE=frontend
rationalbloks-mcp
# or: rationalbloks-mcp-frontend
```

## Available Tools

### Backend Tools (18)

**Read Operations (11):**
- `list_projects` - List all projects
- `get_project` - Get project details
- `get_schema` - Get JSON schema
- `get_user_info` - Get user information
- `get_job_status` - Check deployment status
- `get_project_info` - Detailed project info
- `get_version_history` - Git history
- `get_template_schemas` - Available templates ⭐ Start here!
- `get_subscription_status` - Plan and limits
- `get_project_usage` - Resource metrics
- `get_schema_at_version` - Schema at specific commit

**Write Operations (7):**
- `create_project` - Create new project from schema
- `update_schema` - Update project schema
- `deploy_staging` - Deploy to staging
- `deploy_production` - Deploy to production
- `delete_project` - Delete project
- `rollback_project` - Rollback to previous version
- `rename_project` - Rename project

### Frontend Tools (5)

- `clone_template` - Clone rationalbloksfront template
- `get_template_structure` - Explore template file structure
- `read_template_file` - Read file from template
- `create_backend` - Create backend via Backend tools
- `configure_api_url` - Set API URL in frontend .env

## Fullstack Workflow

Build a complete application in minutes:

### 1. Clone Frontend Template
```
"Use clone_template to create a new project called 'my-app' in ~/projects"
```

### 2. Create Backend API
```
"Create a backend with users and posts tables"
```

### 3. Connect Frontend to Backend
```
"Use configure_api_url to connect my-app to the backend"
```

### 4. Run the App
```bash
cd ~/projects/my-app
npm install
npm run dev
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
| `TRANSPORT` | Transport: stdio, http | `stdio` |

## Entry Points

Three entry points for different use cases:

```bash
# Full mode (all 23 tools)
rationalbloks-mcp

# Backend only (18 tools)
rationalbloks-mcp-backend

# Frontend only (5 tools)
rationalbloks-mcp-frontend
```

## Example Prompts

### Backend Operations

> "List all my RationalBloks projects"

> "Create a project called 'e-commerce' with products, orders, and customers"

> "Deploy my project to staging"

> "Show me the deployment history"

### Frontend Operations

> "Clone the frontend template to ~/projects/my-store"

> "What files are in the template?"

> "Connect my-store to the e-commerce backend"

### Fullstack (Full Mode)

> "Create a complete todo app with a React frontend and REST API"

> "Build me an e-commerce store with product catalog and shopping cart"

## Troubleshooting

### "Command not found"
```bash
pip show rationalbloks-mcp
which rationalbloks-mcp
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

## Architecture

```
rationalbloks-mcp/
├── core/           # Shared infrastructure
│   ├── auth.py     # API key validation
│   ├── transport.py # STDIO + HTTP transport
│   └── server.py   # Base MCP server
├── backend/        # 18 backend tools
│   ├── client.py   # LogicBlok HTTP client
│   └── tools.py    # Tool definitions
└── frontend/       # 5 frontend tools
    ├── client.py   # Template operations
    └── tools.py    # Tool definitions
```

## Support

- **Email:** support@rationalbloks.com
- **Docs:** [rationalbloks.com/docs/mcp](https://rationalbloks.com/docs/mcp)
- **Issues:** [github.com/rationalbloks/rationalbloks-mcp/issues](https://github.com/rationalbloks/rationalbloks-mcp/issues)

## License

Proprietary - Copyright 2026 RationalBloks. All Rights Reserved.
