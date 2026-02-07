# RationalBloks MCP Server

**Deploy production APIs in minutes.** 18 tools for projects, schemas, and deployments.

[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/rationalbloks-mcp.svg)](https://pypi.org/project/rationalbloks-mcp/)

## What Is This?

RationalBloks MCP lets AI agents (Claude, Cursor, etc.) deploy production APIs from a JSON schema. No backend code to write. No infrastructure to manage.

```
"Create a task management API with tasks, projects, and users"
→ 2 minutes later: Production API running on Kubernetes
```

## Installation

```bash
pip install rationalbloks-mcp
```

## Quick Start

### 1. Get Your API Key

Visit [rationalbloks.com/settings](https://rationalbloks.com/settings) and create an API key.

### 2. Configure Your AI Agent

**VS Code / Cursor** - Add to `settings.json`:

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

**Claude Desktop** - Add to `claude_desktop_config.json`:

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

---

## 18 Tools

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
| `get_template_schemas` | Pre-built schema templates |
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

---

## Schema Format

Schemas must be in **FLAT format**:

```json
{
  "tasks": {
    "title": {"type": "string", "max_length": 200, "required": true},
    "status": {"type": "string", "max_length": 50, "enum": ["pending", "done"]},
    "due_date": {"type": "date", "required": false}
  },
  "projects": {
    "name": {"type": "string", "max_length": 100, "required": true}
  }
}
```

### Field Types

| Type | Required Properties |
|------|---------------------|
| `string` | `max_length` |
| `text` | None |
| `integer` | None |
| `decimal` | `precision`, `scale` |
| `boolean` | None |
| `uuid` | None |
| `date` | None |
| `datetime` | None |
| `json` | None |

### Auto-Generated Fields

These are automatic - don't define them:
- `id` (UUID primary key)
- `created_at` (datetime)
- `updated_at` (datetime)

### User Authentication

Use the built-in `app_users` table:

```json
{
  "employee_profiles": {
    "user_id": {"type": "uuid", "foreign_key": "app_users.id", "required": true},
    "department": {"type": "string", "max_length": 100}
  }
}
```

---

## Frontend

For frontend development, use our NPM packages:

```bash
npm install @rationalbloks/frontblok-auth @rationalbloks/frontblok-crud
```

These provide:
- **frontblok-auth**: Authentication, login, tokens, user context
- **frontblok-crud**: Generic CRUD via `getApi().getAll()`, `getApi().create()`, etc.

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RATIONALBLOKS_API_KEY` | Your API key (required) | - |
| `RATIONALBLOKS_TIMEOUT` | Request timeout (seconds) | `30` |
| `RATIONALBLOKS_LOG_LEVEL` | Log level | `INFO` |

---

## Support

- **Documentation:** [rationalbloks.com/docs](https://rationalbloks.com/docs)
- **Email:** support@rationalbloks.com

## License

Proprietary - Copyright 2026 RationalBloks. All Rights Reserved.

<!-- mcp-name: io.github.rationalbloks/rationalbloks-mcp -->
