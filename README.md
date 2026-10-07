# RationalBloks MCP Server

**Deploy production APIs in minutes.** Tools for projects, schemas, deployments, modules, object storage, and graph data — delivered on infrastructure you own (self-host or your own BYOC cluster).

[![License](https://img.shields.io/badge/license-Proprietary-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/rationalbloks-mcp.svg)](https://pypi.org/project/rationalbloks-mcp/)

## What Is This?

RationalBloks MCP lets AI agents (Claude Code, Claude Desktop, Cursor, VS Code, etc.) deploy production APIs from a JSON schema, and deploy and run the frontends and backends built on them. No backend code to write. No infrastructure to manage.

```
"Create a task management API with tasks, projects, and users"
→ 2 minutes later: Production API running on Kubernetes
```

## Installation

```bash
# recommended — no install step; @latest checks for a new release at every start
uvx rationalbloks-mcp@latest

# or install into an environment
pip install rationalbloks-mcp
```

## Quick Start

### 1. Get Your API Key

Visit [rationalbloks.com/settings](https://rationalbloks.com/settings) and create an API key. A key carries scopes: a **read** key reaches only the read tools, a **read + write** key reaches every tool. The server lists only the tools your key may call.

### 2. Configure Your AI Agent

**Claude Code** — remote server (no install):

```bash
claude mcp add --transport http rationalbloks https://mcp.rationalbloks.com/mcp \
  --header "Authorization: Bearer rb_sk_your_key_here"
```

or the local server:

```bash
claude mcp add --env RATIONALBLOKS_API_KEY=rb_sk_your_key_here rationalbloks \
  -- uvx rationalbloks-mcp@latest
```

`--scope project` writes the server to the repository's `.mcp.json` instead, to share it with a team. Keep the key out of the file with `"Authorization": "Bearer ${RATIONALBLOKS_API_KEY}"`: Claude Code expands the variable from each developer's environment.

**VS Code** — add to `.vscode/mcp.json` (Cursor: `.cursor/mcp.json` with a `mcpServers` key):

```json
{
  "servers": {
    "rationalbloks": {
      "command": "uvx",
      "args": ["rationalbloks-mcp@latest"],
      "env": {
        "RATIONALBLOKS_API_KEY": "rb_sk_your_key_here"
      }
    }
  }
}
```

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rationalbloks": {
      "command": "uvx",
      "args": ["rationalbloks-mcp@latest"],
      "env": {
        "RATIONALBLOKS_API_KEY": "rb_sk_your_key_here"
      }
    }
  }
}
```

**Any other client:** point it at `https://mcp.rationalbloks.com/mcp` (Streamable HTTP) with `Authorization: Bearer rb_sk_...`.

### 3. Claude Code Permissions

Every tool that can lose data carries `destructiveHint: true`, and no other tool can lose data. One allow rule covers the server, and ask rules keep a prompt on the tools that can lose data. Claude Code evaluates ask rules before allow rules, so they prompt even though the server is allowed, and in auto mode they still prompt, because they run before the classifier. Add this to `.claude/settings.json` (the project) or `~/.claude/settings.json` (every project):

```json
{
  "permissions": {
    "allow": ["mcp__rationalbloks"],
    "ask": [
      "mcp__rationalbloks__update_schema",
      "mcp__rationalbloks__drop_schema_items",
      "mcp__rationalbloks__deploy_destructive",
      "mcp__rationalbloks__rollback_project",
      "mcp__rationalbloks__delete_project",
      "mcp__rationalbloks__update_graph_schema",
      "mcp__rationalbloks__rollback_graph_project",
      "mcp__rationalbloks__delete_graph_project",
      "mcp__rationalbloks__delete_graph_node",
      "mcp__rationalbloks__delete_graph_relationship",
      "mcp__rationalbloks__set_module_env",
      "mcp__rationalbloks__delete_module"
    ]
  }
}
```

Add `"mcp__rationalbloks__deploy_production"` to `ask` to approve each production release yourself.

**Asked before every change:** allow only the read tools instead. These rules match every read tool and no other:

```json
{
  "permissions": {
    "allow": [
      "mcp__rationalbloks__get_*",
      "mcp__rationalbloks__list_*",
      "mcp__rationalbloks__search_graph_nodes",
      "mcp__rationalbloks__fulltext_search_graph",
      "mcp__rationalbloks__traverse_graph",
      "mcp__rationalbloks__preview_schema_change"
    ]
  }
}
```

**Read-only server:** register a second server with a read key. It lists only the read tools and the platform refuses every other call, so one rule allows all of it:

```bash
claude mcp add --transport http rationalbloks-read https://mcp.rationalbloks.com/mcp \
  --header "Authorization: Bearer rb_sk_your_read_key"
```

```json
{ "permissions": { "allow": ["mcp__rationalbloks-read"] } }
```

**Auto mode** reads `autoMode` only from `~/.claude/settings.json`, managed settings or `--settings`, never from a project's `.claude/settings.json`. If its classifier blocks routine RationalBloks calls, describe your project there, keeping `$defaults` (replace MyProject and apps.yourdomain.com with your project's name and your cluster's domain):

```json
{
  "autoMode": {
    "environment": [
      "$defaults",
      "Key internal services: RationalBloks (MCP server rationalbloks, https://mcp.rationalbloks.com), where our project MyProject runs; its staging environment is for development",
      "Trusted internal domains: rationalbloks.com and *.rationalbloks.com; *.apps.yourdomain.com, where MyProject's APIs and modules are served",
      "Sensitive remote targets: MyProject's production environment"
    ]
  }
}
```

Run `claude auto-mode config` to see the rules in effect, or edit them in `/permissions` (Auto mode tab).

---

## Tools

**Read** tools only read. **Write** tools change something, and never lose data. **Destructive** tools can lose data, and carry `destructiveHint: true`: they replace a whole schema (`update_schema`, `update_graph_schema`), drop, delete, roll back, deploy a plan that drops data (`deploy_destructive`), or overwrite a module's environment (`set_module_env`).

A plan drops data when it drops a table or field, or changes a field's type in a way that rounds or cuts its stored values (a decimal given a smaller scale or turned integer, a datetime turned date). The deploy tools refuse such a plan and name each drop; `deploy_destructive` applies it.

A long operation (create, deploy, rollback, delete, module operations) runs as a job: the tool answers a `job_id`, and `get_job_status` follows it to its result.

### Relational Projects

| Tool | Kind | Description |
|------|------|-------------|
| `list_projects` | read | List all your projects |
| `get_project` | read | Get project details |
| `get_schema` | read | Get the current JSON schema (optionally only some tables or fields) |
| `get_user_info` | read | Get authenticated user info |
| `list_clusters` | read | List your BYOC resource pools (client-owned clusters) |
| `get_job_status` | read | Follow a job (create, deploy, promotion, rollback, deletion, module operation) to its result |
| `list_project_jobs` | read | A project's jobs, newest first, each with its outcome |
| `get_project_info` | read | Detailed project info with K8s status |
| `get_version_history` | read | Git commit history |
| `get_template_schemas` | read | Pre-built schema templates |
| `get_schema_reference` | read | Advanced schema features reference (`__policy__`, `computed`, `__constraints__`, `__audit__`) |
| `get_subscription_status` | read | Plan and usage limits |
| `get_project_usage` | read | CPU/memory metrics |
| `get_project_storage_usage` | read | Object-storage file count and bytes used vs limits |
| `list_project_files` | read | List uploaded files (metadata + public URLs) |
| `get_schema_at_version` | read | Schema at a specific commit |
| `preview_schema_change` | read | Preview a change (patch operations or a whole schema): the migration plan and every drop, saving nothing |
| `create_project` | write | Create a project from a schema (`cluster_id` of one of your BYOC pools; `backend_type` python or rust) |
| `patch_schema` | write | Change part of the schema: add, rename and set tables and fields. Never drops |
| `deploy_staging` | write | Deploy the saved schema to staging. Refuses a plan that drops data |
| `deploy_production` | write | Promote staging to production. Refuses a plan that drops data |
| `redeploy_project` | write | Rebuild and roll out staging from the schema it runs, with no schema change |
| `rename_project` | write | Rename a project |
| `update_schema` | destructive | Replace the whole schema: a table or field it leaves out is dropped by the next deploy |
| `drop_schema_items` | destructive | Drop tables or fields from the saved schema |
| `deploy_destructive` | destructive | Deploy a plan that drops data, to staging or production (relational or graph) |
| `rollback_project` | destructive | Roll schema and code back to a previous version |
| `delete_project` | destructive | Delete a project permanently |

### Graph Projects

| Tool | Kind | Description |
|------|------|-------------|
| `get_graph_schema` | read | Get a graph project's schema |
| `get_graph_template_schemas` | read | Pre-built graph schema templates |
| `get_graph_version_history` | read | Graph schema version history |
| `get_graph_schema_at_version` | read | Schema at a specific version |
| `get_graph_project_info` | read | Graph project info with K8s/Neo4j status |
| `create_graph_project` | write | Create a Neo4j graph project |
| `deploy_graph_staging` | write | Deploy the saved graph schema to staging. Refuses a plan that drops data |
| `deploy_graph_production` | write | Promote graph staging to production. Refuses a plan that drops data |
| `update_graph_schema` | destructive | Replace the whole graph schema: what it leaves out is dropped by the next deploy |
| `rollback_graph_project` | destructive | Roll a graph project back to a previous version |
| `delete_graph_project` | destructive | Delete a graph project |

### Graph Data

| Tool | Kind | Description |
|------|------|-------------|
| `get_graph_node` | read | Get a node by ID |
| `list_graph_nodes` | read | List nodes by entity type |
| `get_node_relationships` | read | Get a node's relationships |
| `search_graph_nodes` | read | Search nodes by property filters |
| `fulltext_search_graph` | read | Full-text search across all fields |
| `traverse_graph` | read | Traverse the graph from a node |
| `get_graph_statistics` | read | Graph statistics (counts) |
| `get_graph_data_schema` | read | The deployed data schema |
| `create_graph_node` | write | Create a node |
| `update_graph_node` | write | Update node properties |
| `create_graph_relationship` | write | Create a relationship |
| `bulk_create_graph_nodes` | write | Create up to 500 nodes |
| `bulk_create_graph_relationships` | write | Create up to 500 relationships |
| `delete_graph_node` | destructive | Delete a node and its relationships |
| `delete_graph_relationship` | destructive | Delete a relationship |

### Modules

A module is one of a project's own frontends (frontblok) or backends (logicblok), built from a GitHub repository and run beside the project.

| Tool | Kind | Description |
|------|------|-------------|
| `list_modules` | read | A project's modules: id, type, repository, URL, status, pods, resources, the image last built |
| `deploy_module` | write | Deploy a new module from a GitHub repository |
| `redeploy_module` | write | Rebuild a module from its repository's default branch head and roll it out |
| `update_module` | write | Rename a module or point it at another repository |
| `freeze_module` | write | Stop a module's pods, remembering how many it ran |
| `unfreeze_module` | write | Start a frozen module's pods again |
| `scale_module` | write | Run 1 or 2 pods of a module |
| `set_module_resources` | write | Set a module's CPU and memory, and rebuild it |
| `set_module_env` | destructive | Set or remove environment variables (merged: variables not named are kept); values are never read back |
| `delete_module` | destructive | Remove a module |

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

`get_schema_reference` covers the advanced features: row policies, computed fields, unique groups (`nulls_not_distinct` for groups with nullable columns), audit trails, and the generated API's scoped deletes.

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
| `RATIONALBLOKS_API_KEY` | Your API key (stdio; HTTP clients send it as a Bearer token per request). Without it the server lists its tools and every call answers how to set it | - |
| `TRANSPORT` | `stdio` or `http` | `stdio` |
| `HOST` / `PORT` | Bind address for `TRANSPORT=http` | `0.0.0.0` / `8000` |
| `LOGICBLOK_URL` | LogicBlok gateway base URL | `https://logicblok.rationalbloks.com` |
| `RATIONALBLOKS_DEBUG` | Print full tracebacks on startup errors | unset |

---

## Support

- **Documentation:** [rationalbloks.com/documentation](https://rationalbloks.com/documentation)
- **Email:** support@rationalbloks.com

## License

Proprietary - Copyright 2026 RationalBloks. All Rights Reserved.

<!-- mcp-name: com.rationalbloks/mcp -->
