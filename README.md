# RationalBloks MCP Server

Connect AI agents (Claude Desktop, Cursor, GPT) to your RationalBloks projects using the Model Context Protocol.

## Installation

```bash
pip install rationalbloks-mcp
```

## Quick Start

### 1. Get Your API Key

1. Go to [rationalbloks.com/settings](https://rationalbloks.com/settings)
2. Scroll to **API Keys** section
3. Click **Create API Key**
4. Enter a name (e.g., "Claude Desktop")
5. Copy the key immediately - it won't be shown again!

### 2. Set Environment Variable

```bash
# Linux/macOS
export RATIONALBLOKS_API_KEY=rb_sk_your_key_here

# Windows (PowerShell)
$env:RATIONALBLOKS_API_KEY = "rb_sk_your_key_here"
```

### 3. Run the Server

```bash
rationalbloks-mcp
```

## Claude Desktop Configuration

Add to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

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

Restart Claude Desktop after saving.

## Cursor IDE Configuration

Add to `.cursor/mcp.json` in your project:

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

## Available Tools

### Read Operations (11 tools)

| Tool | Description |
|------|-------------|
| `list_projects` | List all your projects |
| `get_project` | Get project details |
| `get_schema` | Get project JSON schema |
| `get_user_info` | Get your user info |
| `get_job_status` | Check deployment status |
| `get_project_info` | Detailed project + deployment info |
| `get_version_history` | Git commit history |
| `get_template_schemas` | Available schema templates |
| `get_subscription_status` | Your plan and limits |
| `get_project_usage` | CPU/memory metrics |
| `get_schema_at_version` | Schema at specific commit |

### Write Operations (7 tools)

| Tool | Description |
|------|-------------|
| `create_project` | Create new project from schema |
| `update_schema` | Update project schema |
| `deploy_staging` | Deploy to staging |
| `deploy_production` | Promote to production |
| `delete_project` | Delete a project |
| `rollback_project` | Rollback to previous version |
| `rename_project` | Rename a project |

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

## Troubleshooting

### "RATIONALBLOKS_API_KEY environment variable not set"

Make sure you've exported the API key in your shell:
```bash
export RATIONALBLOKS_API_KEY=rb_sk_your_key_here
```

### "Invalid API key format"

API keys must start with `rb_sk_`. Get a new key from [rationalbloks.com/settings](https://rationalbloks.com/settings).

### "Permission denied - check API key scopes"

Your API key doesn't have the required scope. Create a new key with `read,write` permissions.

### "Rate limit exceeded"

Wait a moment and try again. Default limit is 60 requests/minute.

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
        "x-api-key": "rb_sk_your_key_here"
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
