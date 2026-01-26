# RationalBloks MCP Server

**Enterprise-grade Model Context Protocol (MCP) server for RationalBloks** - Connect AI agents (Claude Desktop, Cursor, VS Code Copilot) to programmatically manage backend APIs through natural language.

[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Installation

```bash
uv pip install rationalbloks-mcp
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

**Location:**
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

## Available Tools

### Read Operations (11)
- `list_projects` - List all projects
- `get_project` - Get project details
- `get_schema` - Get JSON schema
- `get_user_info` - Get user information
- `get_job_status` - Check deployment status
- `get_project_info` - Detailed project info
- `get_version_history` - Git history
- `get_template_schemas` - Available templates
- `get_subscription_status` - Plan and limits
- `get_project_usage` - Metrics
- `get_schema_at_version` - Schema at commit

### Write Operations (7)
- `create_project` - Create new project
- `update_schema` - Update schema
- `deploy_staging` - Deploy to staging
- `deploy_production` - Deploy to production
- `delete_project` - Delete project
- `rollback_project` - Rollback version
- `rename_project` - Rename project

## Authentication

Uses **OAuth2 Bearer Token** (RFC 6750):

```
Authorization: Bearer rb_sk_your_key_here
```

All API keys follow format: `rb_sk_` + 43 characters

## Architecture

### Local Mode (STDIO)
- For VS Code, Cursor, Claude Desktop
- JSON-RPC over stdin/stdout
- Fast, private, offline-capable

### Cloud Mode (HTTP/SSE)
- For Smithery, web agents
- Streamable HTTP with Server-Sent Events
- Works anywhere with internet

## Testing

```bash
# Test command
export RATIONALBLOKS_API_KEY=rb_sk_your_key
rationalbloks-mcp

# Test gateway
curl https://logicblok.rationalbloks.com/api/mcp/health \
  -H "Authorization: Bearer rb_sk_your_key"
```

## Troubleshooting

### "Command not found"
```bash
pip show rationalbloks-mcp
which rationalbloks-mcp
```

### "API key required"
Check format: must start with `rb_sk_`

### Tools not loading
1. Check IDE Output panel for errors
2. Reload window
3. Verify settings.json syntax

## Support

- **Email:** support@rationalbloks.com
- **Docs:** [rationalbloks.com/docs/mcp](https://rationalbloks.com/docs/mcp)

## Example Usage with Claude

Try these prompts:

> "List all my RationalBloks projects"

> "Create a new project called 'my-store' with customers and orders tables"

> "Show me the schema for project abc123"

> "Deploy my-store to staging"

> "Show me the deployment history for my-store"

> "Rollback my-store to the previous version"

## API Key Scopes

| Scope | Permissions |
|-------|-------------|
| `read` | View projects, schemas, status |
| `write` | Create, update, deploy, delete |
| `admin` | Full access (includes admin operations) |

Default scope is `read,write` which covers all common operations.

## Rate Limiting

- Default: 60 requests per minute per API key
- Configurable per API key
- 429 responses include retry guidance

## Security

- API keys start with `rb_sk_` prefix
- Keys are hashed in storage (only prefix visible after creation)
- Each key can be revoked independently
- Full audit logging of all operations

## Schema Examples

### E-Commerce Store

```json
{
  "schema": {
    "customers": {
      "name": { "type": "string", "required": true },
      "email": { "type": "string", "format": "email", "unique": true },
      "phone": { "type": "string" },
      "created_at": { "type": "datetime", "default": "now" }
    },
    "products": {
      "name": { "type": "string", "required": true },
      "price": { "type": "decimal", "precision": 10, "scale": 2 },
      "sku": { "type": "string", "unique": true },
      "stock": { "type": "integer", "default": 0 },
      "category": { "type": "string" }
    },
    "orders": {
      "customer_id": { "type": "reference", "to": "customers" },
      "total": { "type": "decimal", "precision": 10, "scale": 2 },
      "status": { "type": "enum", "values": ["pending", "paid", "shipped", "delivered"] },
      "created_at": { "type": "datetime", "default": "now" }
    },
    "order_items": {
      "order_id": { "type": "reference", "to": "orders" },
      "product_id": { "type": "reference", "to": "products" },
      "quantity": { "type": "integer", "required": true },
      "unit_price": { "type": "decimal", "precision": 10, "scale": 2 }
    }
  }
}
```

### Team Collaboration

```json
{
  "schema": {
    "users": {
      "name": { "type": "string", "required": true },
      "email": { "type": "string", "format": "email", "unique": true },
      "role": { "type": "enum", "values": ["admin", "member", "viewer"] }
    },
    "teams": {
      "name": { "type": "string", "required": true },
      "description": { "type": "text" }
    },
    "tasks": {
      "title": { "type": "string", "required": true },
      "description": { "type": "text" },
      "team_id": { "type": "reference", "to": "teams" },
      "assigned_to": { "type": "reference", "to": "users" },
      "status": { "type": "enum", "values": ["todo", "in_progress", "done"] },
      "due_date": { "type": "date" }
    }
  }
}
```

## Deployment Workflow

1. **Create Project** → Generates staging environment
2. **Update Schema** → Modify your data model
3. **Deploy Staging** → Test your changes
4. **Deploy Production** → Promote when ready
5. **Rollback** → Revert if needed

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Development │ →  │   Staging    │ →  │  Production  │
│   (Schema)   │    │   (Test)     │    │   (Live)     │
└──────────────┘    └──────────────┘    └──────────────┘
                            ↑
                            │
                    ┌───────┴───────┐
                    │   Rollback    │
                    └───────────────┘
```

## HTTP Transport (Remote)

Connect to the hosted MCP server at `https://mcp.rationalbloks.com`:

```json
{
  "mcpServers": {
    "rationalbloks-remote": {
      "transport": "sse",
      "url": "https://mcp.rationalbloks.com/sse",
      "headers": {
        "Authorization": "Bearer rb_sk_your_key_here"
      }
    }
  }
}
```

## Smithery Installation

Install via Smithery CLI for one-click setup:

```bash
npx @smithery/cli install @rationalbloks/mcp
```

## What is RationalBloks?

RationalBloks is a Backend-as-a-Service platform that generates complete backend APIs from JSON schemas. When you connect via MCP:

- **AI agents** can create and manage your backends
- **No coding required** - just describe your data model
- **Automatic APIs** - REST endpoints generated instantly
- **Database included** - PostgreSQL managed for you
- **Staging + Production** - Full deployment pipeline

## License

Copyright © 2026 RationalBloks. All Rights Reserved.

This is proprietary software. See [LICENSE](LICENSE) for details.

## Links

- [RationalBloks Platform](https://rationalbloks.com)
- [MCP Server Status](https://mcp.rationalbloks.com/health)
- [Documentation](https://rationalbloks.com/docs)
- [Support](https://rationalbloks.com/support)
- [Smithery](https://smithery.ai)
