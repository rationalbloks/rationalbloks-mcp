# ============================================================================
# RATIONALBLOKS MCP - BACKEND TOOLS
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# The tools, in four lists (the gateway, logicblok/mcp_gateway.py, serves each one and decides what it
# does; logicblok/tests/test_api_keys.py holds these lists to its tables):
#   BACKEND_TOOLS     relational projects (the preview, the destructive deploy and the redeploy also take
#                     graph ones)
#   GRAPH_TOOLS       graph projects' schemas
#   GRAPH_DATA_TOOLS  the data of a deployed graph project
#   MODULE_TOOLS      a project's own frontends and backends
# api_reference writes them out by kind for the rationalbloks://docs/api-reference resource.
#
# ANNOTATIONS. One rule for every tool, so a client that decides by them decides right:
#   readOnlyHint     true exactly for the tools a read key may call (the gateway's read scope)
#   destructiveHint  true when a call can delete something (a project, module, table, field, node,
#                    relationship or environment variable) or replace a whole (a whole schema, a deploy
#                    that drops data, a rollback); false when a call only adds, or changes the values it
#                    names. Risk is in the tool name, never in an argument: a client's permission rules
#                    match names, so every destructive change is a tool of its own (drop_schema_items,
#                    deploy_destructive).
#   idempotentHint   true when calling again with the same arguments changes nothing more
#   openWorldHint    false: every tool acts on the caller's own RationalBloks account
# ============================================================================

from typing import Any

from mcp.types import Prompt, PromptArgument, PromptMessage, GetPromptResult, TextContent

from .._version import __version__
from ..core import BaseMCPServer
from .client import LogicBlokClient

# Public API
__all__ = [
    "BACKEND_TOOLS",
    "GRAPH_TOOLS",
    "GRAPH_DATA_TOOLS",
    "MODULE_TOOLS",
    "INFRASTRUCTURE_TOOLS",
    "BACKEND_PROMPTS",
    "GRAPH_PROMPTS",
    "BackendMCPServer",
    "create_backend_server",
]


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

# The refusals every operation that starts a job can answer, stated once
PLATFORM_UPDATE_REFUSAL = (" While RationalBloks is being updated, the call is refused with 'RationalBloks is being "
                           "updated': call it again in a few minutes.")
BUSY_PROJECT_REFUSAL = (" One operation runs on a project at a time: while another runs, the call is refused and the "
                        "refusal names the running job; wait for it with get_job_status, then call again." + PLATFORM_UPDATE_REFUSAL)
BUSY_MODULE_REFUSAL = (" One operation runs on a module at a time, and none beside an operation on its project: "
                       "the refusal names the running job; wait for it with get_job_status, then call again." + PLATFORM_UPDATE_REFUSAL)

# What a deploy tool answers a plan that drops data, stated once
DESTRUCTIVE_PLAN_REFUSAL = (" A plan that drops data is refused, naming every table, field, entity or relationship it "
                            "would drop, and every field whose type change rounds or cuts its values (a decimal with a "
                            "smaller scale or turned integer, a datetime turned date): deploy_destructive applies it, a "
                            "tool of its own so a client asks before it runs.")


BACKEND_TOOLS = [
    # --- READ OPERATIONS ---
    {
        "name": "list_projects",
        "title": "List Projects",
        "description": "List all your RationalBloks projects with their status and URLs",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_project",
        "title": "Get Project Details",
        "description": "Get detailed information about a specific project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_schema",
        "title": "Get Project Schema",
        "description": "Get the JSON schema definition of a project in FLAT format. Returns the schema structure where each table name maps directly to field definitions. This is the same format required for create_project and update_schema. USE CASES: Review current schema before making updates, copy schema as template for new projects, verify schema structure after deployment, learn the correct schema format by example. The returned schema will be in FLAT format: {table_name: {field_name: {type, properties}}}. The response also says whether this saved schema is the deployed one: saved_schema_deployed is true when the last deploy applied it, false when it was saved after the last deploy (undeployed_changes then lists what deploying it would change), and null when no deployed schema is on record. A LARGE SCHEMA: pass tables or fields to read only the part you are about to change — the answer's 'version' is the whole schema's either way, so a slice is enough to patch it with patch_schema(expected_version=...).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "tables": {"type": "array", "items": {"type": "string"}, "description": "Read only these tables, whole (e.g. [\"parameters\"]). A table the schema does not hold is refused."},
                "fields": {"type": "array", "items": {"type": "string"}, "description": "Read only these fields, each written 'table.field' (e.g. [\"parameters.is_clock\"]); their table's own keys come with them."}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_user_info",
        "title": "Get User Info",
        "description": "Get information about the authenticated user",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "list_clusters",
        "title": "List Resource Pools",
        "description": "List your registered BYOC resource pools (client-owned Kubernetes clusters). Each returned cluster has an 'id' you MUST pass as create_project's cluster_id to deploy a project onto your own infrastructure — owned hosting is retired, so every project we operate runs on your own cluster. Registering a pool is a UI action (create a bare Ubuntu box, authorise the key we generate, then we provision it into a cluster automatically) — this tool only lists pools you already registered, it never handles cluster credentials.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_job_status",
        "title": "Get Job Status",
        "description": "Check the status of a job (a create, deploy, promotion, rollback, deletion or module operation). STATUS VALUES: pending (queued), processing (in progress), completed (success), failed. Call it until the status is completed or failed: every job ends, since a job whose server stopped is failed within about three minutes, and a deploy can take up to 15 minutes. A module job names its module_code, and a completed module build's result names the image it built (its commit). If status is 'failed', read failure_side and error: 'customer' means the project's input is proven the cause (an invalid schema, data the new schema does not fit, a change the resource pool cannot hold), and error says what to change; 'platform' means no input of the project is known to cause it: report it to RationalBloks rather than changing the schema.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Job ID a create, deploy, promotion, rollback, deletion or module operation answered"}
            },
            "required": ["job_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "list_project_jobs",
        "title": "List Project Jobs",
        "description": "List a project's jobs, newest first: every create, deploy, promotion, rollback, resource change and module operation, each with its status, error, failure_side and when it started and ended. A job's record is kept for the life of the project, so this is how to find out what an operation did when you no longer have its job_id (after an interruption, or in a later session): the first job of the job_type you want is the latest. Read older jobs a page at a time with offset; a page shorter than limit is the last.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "limit": {"type": "integer", "description": "Max jobs to return (1-1000, default 100)"},
                "offset": {"type": "integer", "description": "Jobs to skip, newest first (default 0)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_project_info",
        "title": "Get Project Info",
        "description": "Get detailed project info including deployment status and resource usage. DEPLOYMENT STATUS: Running (healthy), Pending (starting), CrashLoopBackOff (init container failed - usually schema format error), ImagePullBackOff (image build failed). TROUBLESHOOTING: If status is CrashLoopBackOff, the schema is likely in wrong format (nested 'fields' key or missing 'type' properties). Use get_schema to review current schema. If replicas show 0/2, the init container (migration runner) is failing. This is almost always a schema format issue. RETURNS THE LIVE API URL: staging.url and production.url carry the deployed base URL for each environment (append /docs for the interactive OpenAPI docs); github.url is the generated repository. create_project does NOT return a URL, so this is the tool to call once get_job_status reports the deployment finished.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_version_history",
        "title": "Get Version History",
        "description": "Get the deployment and version history (git commits) for a project. Shows all schema changes with commit SHA, timestamp, and message. USE CASES: Review what changed between deployments, find the last working version before issues started, get commit SHA for rollback_project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_template_schemas",
        "title": "Get Template Schemas",
        "description": "Get pre-built template schemas for common use cases. ⭐ USE THIS FIRST when creating a new project! Templates show the CORRECT schema format with: proper FLAT structure (no 'fields' nesting), every field has a 'type' property, foreign key relationships configured correctly, best practices for field naming and types. Available templates: Start from Scratch (every field type), Team Collaboration (workspaces, channels, messages, tasks), E-Commerce Store (customer profiles, products, orders and their line items, reviews, shipments). Each entry's 'schema' goes to create_project as is or adapted; its 'tables' notes say how each table is authorized. TIP: Study these templates to understand the correct schema format before creating custom schemas.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_schema_reference",
        "title": "Get Schema Features Reference",
        "description": "Get the reference for ADVANCED schema features the templates do not show — read this before adding authorization or derived fields to a schema. Covers: __policy__ (relationship-based read/write authorization with single- and multi-hop membership paths, and the rules that decide whether adopting it is safe — it replaces creator-ownership per table and fails closed on a null link), computed columns (read-only values derived from other columns), __constraints__ (composite uniqueness), __audit__ (append-only audit log), __admin_write__ (a table only admins write), how user foreign keys are attributed on create, and reading many rows in one request with <field>__in=a,b,c (the values separated by commas only).",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_subscription_status",
        "title": "Get Subscription Status",
        "description": "Get your subscription tier, limits, and usage",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_project_usage",
        "title": "Get Project Usage",
        "description": "Get resource usage metrics (CPU, memory) for a project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_project_storage_usage",
        "title": "Get Project Storage Usage",
        "description": "Get object-storage usage for a project: file count and bytes used against the plan limits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: production)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "list_project_files",
        "title": "List Project Files",
        "description": "List a project's uploaded files (metadata + public URLs), most recent first. Inspection only — files are not streamed through MCP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: production)"},
                "limit": {"type": "integer", "description": "Max files to return (1-1000, default 100)"},
                "offset": {"type": "integer", "description": "Pagination offset (default 0)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_schema_at_version",
        "title": "Get Schema at Version",
        "description": "Get the schema as it was at a specific version/commit",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "version": {"type": "string", "description": "Commit SHA of the version"}
            },
            "required": ["project_id", "version"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "preview_schema_change",
        "title": "Preview Schema Change",
        "description": """Preview a schema change, saving nothing: the one way to see what a change would do before it is saved.

Pass ONE of:
• operations: the operations patch_schema or drop_schema_items would apply (relational projects)
• schema: a whole schema in place of the saved one (relational or graph projects)

ANSWER: 'applied' (for operations), 'diff' (every property saving it would change, by path), 'summary' and 'plan' (the migration the next deploy would then run, every table, field, entity or relationship it drops named), and 'version' (the saved schema's: pass it as expected_version to the save that follows, so it is refused if someone saved meanwhile).

A relational schema the deploy would refuse is refused here, with the reason.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "operations": {"type": "array", "items": {"type": "object"}, "description": "A change to part of a relational schema, as patch_schema or drop_schema_items take it. Pass this or schema."},
                "schema": {"type": "object", "description": "A whole schema in place of the saved one (relational or graph). Pass this or operations."}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "create_project",
        "title": "Create Project",
        "description": """Create a new RationalBloks project (a PostgreSQL REST API) from a JSON schema, on one of your resource pools.

⚠️ CRITICAL RULES - READ BEFORE CREATING SCHEMA:

1. FLAT FORMAT (REQUIRED):
   ✅ CORRECT: {"orders": {"total": {"type": "decimal", "precision": 10, "scale": 2}}}
   ❌ WRONG: {"orders": {"fields": {...}}} — never nest under 'fields'

2. EVERY field has a "type":
   string (MUST have max_length), text, integer, decimal (precision, scale), boolean, uuid, date,
   datetime (NOT "timestamp"), json, and the PostgreSQL arrays uuid_array, integer_array, text_array,
   float_array (GIN-indexed: @> contains, <@ contained_by, && overlaps)

3. AUTOMATIC FIELDS (DON'T define): id, created_at, updated_at

4. USERS: NEVER create users/customers/employees tables with email or password. Link to the built-in
   app_users table: {"user_id": {"type": "uuid", "foreign_key": "app_users.id"}}. A table with such a
   field is owner-scoped: each user sees their own rows.

5. FIELD OPTIONS: required, unique, default, enum, foreign_key ("table.id"), on_delete (cascade,
   set_null, restrict, no_action), nullable, index, description, write_only, computed.
   Advanced features (__policy__, computed columns, __constraints__, __audit__): get_schema_reference.

BACKEND ENGINE (backend_type): "python" (FastAPI, default) or "rust" (Axum: faster cold starts, lower memory).

WORKFLOW:
1. get_template_schemas FIRST to see valid examples
2. create_project with a cluster_id from list_clusters
3. Poll get_job_status with the returned job_id (2-5 minutes)
4. get_project_info gives the live URL""" + PLATFORM_UPDATE_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name"},
                "schema": {"type": "object", "description": "JSON schema in FLAT format (table_name → field_name → properties). Every field MUST have a 'type' property. Use get_template_schemas to see valid examples."},
                "backend_type": {"type": "string", "enum": ["python", "rust"], "description": "Backend engine: 'python' (FastAPI, default) or 'rust' (Axum, faster). Default: python"},
                "cluster_id": {"type": "string", "description": "REQUIRED — BYOC resource pool ID (from list_clusters) to deploy this project onto your own cluster. Owned hosting is retired: a project we operate must run on your own infrastructure. Register a pool via the Resource Pools UI first, then pass its id here."}
            },
            "required": ["name", "schema", "cluster_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "update_schema",
        "title": "Update Schema",
        "description": """Replace a project's WHOLE schema (saves to database, does NOT deploy). DESTRUCTIVE: a table or field the schema leaves out is dropped by the next deploy.

For a new data model or a template. To change part of a schema use patch_schema, and drop_schema_items to drop; sending back a large schema to change one field risks changing something else on the way.

⚠️ Follow ALL rules from create_project:
• FLAT format (no 'fields' nesting)
• string: max_length (default 255)
• decimal: precision + scale (default 10, 2)
• Use "datetime" NOT "timestamp"
• DON'T define: id, created_at, updated_at
• NEVER create users/customers/employees tables (use app_users)

⚠️ MIGRATION RULES:
• New fields MUST be "required": false OR have "default" value
• Cannot add required field without default to existing tables

WORKFLOW:
1. get_schema to see the current schema (its 'version' pins the save)
2. preview_schema_change with the new schema: check 'diff' and 'plan'
3. update_schema (pass expected_version to be refused if someone else saved meanwhile)
4. deploy_staging, then get_job_status

A schema the deploy would refuse is refused here, and nothing is saved. The answer carries 'diff', 'plan' and the new 'version'.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "schema": {"type": "object", "description": "New JSON schema in FLAT format (table_name → field_name → properties) — the WHOLE schema. Every field MUST have a 'type' property."},
                "expected_version": {"type": "string", "description": "The 'version' a get_schema read answered. The save is refused (409) when the saved schema changed since, so two editors never overwrite each other silently."}
            },
            "required": ["project_id", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "patch_schema",
        "title": "Patch Schema",
        "description": """Change PART of a project's schema without dropping any of it (saves to database, does NOT deploy).

Send only the change. The server applies it to the saved schema, in order and all together, and keeps
every table and field it does not touch — including their identity, so a rename stays a rename and the
column keeps its data.

OPERATIONS (each one small object, applied in the order given):
• {"op": "add_table", "table": "clocks", "definition": {...}}      new table, same FLAT rules as create_project
• {"op": "rename_table", "table": "clocks", "to": "timers"}
• {"op": "add_field", "table": "assets", "field": "serial", "definition": {"type": "string", "max_length": 64}}
• {"op": "rename_field", "table": "parameters", "field": "is_clock", "to": "clock_kind"}
• {"op": "set_field", "table": "assets", "field": "name", "properties": {"max_length": 300}}   merges; a property set to null is removed
• {"op": "set_table", "table": "assets", "properties": {"__audit__": true}}   __policy__, __constraints__, __audit__, __admin_write__

Dropping a table or field is drop_schema_items, a tool of its own.

ALL OR NOTHING: an operation that cannot be applied — a table or field that is not there, a name
already taken, a schema the deploy would refuse — refuses the whole patch, naming the operation, and
nothing is saved.

EVERY ANSWER IS A DIFF: 'applied' (what each operation did), 'diff' (every changed property by path),
'summary' and 'plan' (the migration a deploy would then run), and 'version' (the schema's version
after the change).

WORKFLOW:
1. get_schema with tables/fields to read the part you are changing (its 'version' is the whole schema's)
2. preview_schema_change with the operations: check 'diff' and 'plan'
3. patch_schema with the same operations (pass expected_version to be refused if someone else saved meanwhile)
4. deploy_staging, then get_job_status""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "operations": {"type": "array", "items": {"type": "object"}, "description": "The operations, applied in order and all together. See the tool description for every op and its fields."},
                "expected_version": {"type": "string", "description": "The 'version' a get_schema read answered. The patch is refused (409) when the saved schema changed since, so two editors never overwrite each other silently."}
            },
            "required": ["project_id", "operations"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "drop_schema_items",
        "title": "Drop Tables or Fields",
        "description": """Drop tables or fields from a project's saved schema (saves to database, does NOT deploy). DESTRUCTIVE: the next deploy drops their data.

OPERATIONS (applied in order and all together):
• {"op": "drop_table", "table": "clocks"}
• {"op": "drop_field", "table": "parameters", "field": "is_clock"}

A drop that cannot be applied (a table or field that is not there, a schema the deploy would refuse, such as a field another reads) refuses them all, naming it, and nothing is saved. The answer carries 'applied', 'diff', 'plan' and the new 'version'.

WORKFLOW:
1. preview_schema_change with the same operations: check 'diff' and 'plan'
2. drop_schema_items (pass expected_version to be refused if someone else saved meanwhile)
3. deploy_staging refuses the plan and names its drops; deploy_destructive applies it, then get_job_status""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "operations": {"type": "array", "items": {"type": "object"}, "description": "The drops: drop_table(table) and drop_field(table, field) operations, applied in order and all together."},
                "expected_version": {"type": "string", "description": "The 'version' a get_schema read answered. The drop is refused (409) when the saved schema changed since."}
            },
            "required": ["project_id", "operations"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "deploy_staging",
        "title": "Deploy to Staging",
        "description": "Deploy a project's saved schema to the staging environment. This triggers: (1) Schema validation, (2) Docker image build, (3) GitHub commit, (4) Kubernetes deployment, (5) Database migrations. The operation is ASYNCHRONOUS - it returns immediately with a job_id. Use get_job_status with the job_id to monitor progress. Deployment typically takes 2-5 minutes depending on schema complexity. If deployment fails, read the job's error first: one that starts with 'RationalBloks platform error' is the platform's, not the schema's. Otherwise check: (1) Schema format is FLAT (no 'fields' nesting), (2) Every field has a 'type' property, (3) Foreign keys reference existing tables, (4) No PostgreSQL reserved words in table/field names. Use get_project_info to see if the deployment succeeded." + DESTRUCTIVE_PLAN_REFUSAL + BUSY_PROJECT_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "deploy_production",
        "title": "Deploy to Production",
        "description": "Promote staging to production (requires a paid plan): production's database migrates from the schema it runs to the one staging runs, and production runs staging's build. With staging unchanged since the last promotion, it rebuilds production with no schema change. The operation is ASYNCHRONOUS: poll the returned job_id with get_job_status." + DESTRUCTIVE_PLAN_REFUSAL + BUSY_PROJECT_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "deploy_destructive",
        "title": "Deploy a Plan That Drops Data",
        "description": "Deploy a plan that drops data, of a relational or a graph project. DESTRUCTIVE: the tables, fields, entities or relationships the plan drops lose their data. environment 'staging' deploys the saved schema, 'production' promotes staging. Use it only after a deploy tool (deploy_staging, deploy_production, deploy_graph_staging, deploy_graph_production) refused the plan, naming its drops, and those drops are intended. The operation is ASYNCHRONOUS: poll the returned job_id with get_job_status." + BUSY_PROJECT_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID), relational or graph"},
                "environment": {"type": "string", "enum": ["staging", "production"], "description": "staging (deploys the saved schema) or production (promotes staging)"}
            },
            "required": ["project_id", "environment"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "redeploy_project",
        "title": "Redeploy Project",
        "description": "Rebuild and roll out a project's staging environment from the schema it runs, with NO schema change, for a relational or a graph project: the current platform release, the project's settings (email, admin users) and its environment take effect. Refused (409) when the saved schema holds changes the last deploy did not apply (deploy_staging deploys those) or when nothing was deployed yet; a save that lands meanwhile is refused rather than deployed. deploy_production rebuilds production the same way when staging runs what production runs. The operation is ASYNCHRONOUS: poll the returned job_id with get_job_status." + BUSY_PROJECT_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID), relational or graph"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "delete_project",
        "title": "Delete Project",
        "description": "Delete a project (removes GitHub repo, K8s deployments, and database). It runs as a job: poll the returned job_id with get_job_status until it is completed." + BUSY_PROJECT_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "rollback_project",
        "title": "Rollback Project",
        "description": "Rollback a project to a previous version. ⚠️ WARNING: This reverts schema AND code to the specified commit. Database data is NOT rolled back. Use get_version_history to find the commit SHA of the version you want to rollback to. After rollback, use get_job_status to monitor the redeployment. Rollback is useful when a schema change breaks deployment." + BUSY_PROJECT_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "version": {"type": "string", "description": "Commit SHA or version to rollback to"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "version"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "rename_project",
        "title": "Rename Project",
        "description": "Rename a project (changes display name, not project_code)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "name": {"type": "string", "description": "New display name for the project"}
            },
            "required": ["project_id", "name"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
]


# ============================================================================
# GRAPH TOOLS (Neo4j graph database projects)
# ============================================================================

GRAPH_TOOLS = [
    # ========================================================================
    # READ TOOLS
    # ========================================================================
    {
        "name": "get_graph_schema",
        "title": "Get Graph Schema",
        "description": "Get the graph schema definition of a project. Returns the hierarchical schema with nodes (entities) and relationships. Graph schemas define entity hierarchies and typed relationships — a different format than relational flat-table schemas. The response also says whether this saved schema is the deployed one: saved_schema_deployed is true when the last deploy applied it, false when it was saved after the last deploy (undeployed_changes then lists what deploying it would change), and null when no deployed schema is on record.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_graph_template_schemas",
        "title": "Get Graph Template Schemas",
        "description": """Get pre-built graph template schemas for common use cases. ⭐ USE THIS FIRST when creating a new graph project! Templates show the CORRECT graph schema format with: proper node definitions (description, flat_labels, schema with flat field definitions), relationship configurations (from, to, cardinality, data_schema), and hierarchical entity nesting. Available templates: Start from Scratch (hierarchy, flat labels, every field type), Social Network (people, organizations, content, follows), Knowledge Graph (topic hierarchy, articles, authors, concepts), Product Catalog (products, categories, suppliers, reviews). Each entry's 'schema' goes to create_graph_project as is or adapted. TIP: Study these templates to understand the correct graph schema format before creating custom schemas.""",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_graph_version_history",
        "title": "Get Graph Version History",
        "description": "Get the deployment and version history for a graph project. Shows all schema changes with commit SHAs, timestamps, version numbers, and messages. Use this to find a specific version for rollback operations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_graph_schema_at_version",
        "title": "Get Graph Schema at Version",
        "description": "Get the graph schema as it existed at a specific version/commit. Use get_graph_version_history to find commit SHAs. Useful for comparing schemas across versions or auditing changes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "version": {"type": "string", "description": "Commit SHA of the version to retrieve"}
            },
            "required": ["project_id", "version"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_graph_project_info",
        "title": "Get Graph Project Info",
        "description": "Get detailed graph project information including Kubernetes deployment status, Neo4j database health, pod status, and resource usage. Use this after deployment to verify the graph project is running correctly.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    # ========================================================================
    # WRITE TOOLS
    # ========================================================================
    {
        "name": "create_graph_project",
        "title": "Create Graph Project",
        "description": """Create a new Neo4j graph database project from a hierarchical JSON schema.

⚠️ GRAPH SCHEMA FORMAT — READ BEFORE CREATING:

Graph schemas define nodes (entities) and relationships, NOT flat database tables.
Each field is a dict with "type" and optional "required": true (defaults to false).

SCHEMA STRUCTURE:
{
  "nodes": {
    "EntityName": {
      "description": "What this entity represents",
      "flat_labels": ["AdditionalLabel"],
      "schema": {
        "field_name": {"type": "string", "required": true},
        "other_field": {"type": "integer"}
      }
    }
  },
  "relationships": {
    "RELATIONSHIP_TYPE": {
      "from": "EntityName",
      "to": "OtherEntity",
      "cardinality": "MANY_TO_MANY",
      "data_schema": {
        "field_name": {"type": "date"}
      }
    }
  }
}

FIELD TYPES: string, integer, float, boolean, date, json

CARDINALITY OPTIONS: ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY

HIERARCHICAL NODES: nest an entity inside its parent entity (beside "description", "flat_labels"
and "schema") to create a type hierarchy; the child inherits the parent's labels:
  "Animal": {"description": "...", "schema": {...}, "Dog": {"description": "...", "schema": {...}}}

RULES:
1. "nodes" key is REQUIRED — must contain at least one entity
2. Each entity needs "description" and "schema" with field definitions
3. Each field is {"type": "...", "required": true/false} — required defaults to false
4. Relationship "from"/"to" must reference defined node names
5. Relationship types should be UPPER_SNAKE_CASE
6. Entity names should be PascalCase
7. Automatic fields (id, created_at, updated_at) are NOT needed

WORKFLOW:
1. get_graph_template_schemas FIRST to see valid examples
2. create_graph_project with a cluster_id from list_clusters
3. Poll get_job_status with the returned job_id (2-5 minutes)""" + PLATFORM_UPDATE_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name"},
                "schema": {"type": "object", "description": "Graph schema with 'nodes' and optionally 'relationships' keys. Use get_graph_template_schemas to see valid examples."},
                "cluster_id": {"type": "string", "description": "REQUIRED — BYOC resource pool ID (from list_clusters) to deploy this graph project onto your own cluster. Owned hosting is retired: a project we operate must run on your own infrastructure. Register a pool via the Resource Pools UI first, then pass its id here."}
            },
            "required": ["name", "schema", "cluster_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "update_graph_schema",
        "title": "Update Graph Schema",
        "description": """Replace a graph project's WHOLE schema (saves to database, does NOT deploy). DESTRUCTIVE: an entity, relationship or field the schema leaves out is deleted by the next deploy.

⚠️ Follow ALL rules from create_graph_project:
• Must have "nodes" key with at least one entity
• Each entity needs "description" and "schema" with field definitions
• Each field is {"type": "...", "required": true/false} — required defaults to false
• Relationships need "from", "to", and "cardinality"
• Field types: string, integer, float, boolean, date, json
• Relationship types should be UPPER_SNAKE_CASE
• Entity names should be PascalCase

WORKFLOW:
1. get_graph_schema to see the current schema (its 'version' pins the save)
2. preview_schema_change with the new schema: check 'diff' and 'plan'
3. update_graph_schema (pass expected_version to be refused if someone else saved meanwhile)
4. deploy_graph_staging, then get_job_status""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "schema": {"type": "object", "description": "New graph schema with 'nodes' and optionally 'relationships' keys — the WHOLE schema."},
                "expected_version": {"type": "string", "description": "The 'version' a get_graph_schema read answered. The save is refused (409) when the saved schema changed since."}
            },
            "required": ["project_id", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "deploy_graph_staging",
        "title": "Deploy Graph to Staging",
        "description": "Deploy a graph project's saved schema to the staging environment. This triggers: (1) Schema validation, (2) Neo4j entity code generation, (3) Docker image build, (4) GitHub commit, (5) Kubernetes deployment with Neo4j instance. The operation is ASYNCHRONOUS — returns immediately with a job_id. Use get_job_status to monitor progress. Deployment typically takes 2-5 minutes. Use get_graph_project_info to verify deployment succeeded." + DESTRUCTIVE_PLAN_REFUSAL + BUSY_PROJECT_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "deploy_graph_production",
        "title": "Deploy Graph to Production",
        "description": "Promote graph staging to production. Creates a separate production Neo4j instance with its own credentials and database. Requires paid plan." + DESTRUCTIVE_PLAN_REFUSAL + BUSY_PROJECT_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "delete_graph_project",
        "title": "Delete Graph Project",
        "description": "Delete a graph project (removes GitHub repo, K8s deployments, Neo4j database, and credentials). It runs as a job: poll the returned job_id with get_job_status until it is completed." + BUSY_PROJECT_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "rollback_graph_project",
        "title": "Rollback Graph Project",
        "description": "Rollback a graph project to a previous version. ⚠️ WARNING: This reverts schema AND code to the specified commit. Neo4j data is NOT rolled back. Use get_graph_version_history to find the commit SHA of the version you want to rollback to. After rollback, the graph API will be redeployed with the old schema." + BUSY_PROJECT_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "version": {"type": "string", "description": "Commit SHA to rollback to"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "version"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
    },
]


# ============================================================================
# GRAPH DATA TOOLS (operating on graph data via deployed APIs)
# ============================================================================

GRAPH_DATA_TOOLS = [
    # ========================================================================
    # NODE CRUD
    # ========================================================================
    {
        "name": "create_graph_node",
        "title": "Create Graph Node",
        "description": """Create a single node in a deployed graph project.

REQUIRES: Project must be deployed (use deploy_graph_staging first).

The entity_type must match an entity key from the project schema.
Use get_graph_data_schema to see available entity types and their fields.

Example:
  entity_type: "person"
  entity_id: "alan-turing-001"
  data: {"name": "Alan Turing", "birth_year": 1912, "field": "Computer Science"}

The entity_id is your unique identifier — use meaningful IDs for knowledge graphs.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "entity_type": {"type": "string", "description": "Entity key (e.g., 'person', 'concept')"},
                "entity_id": {"type": "string", "description": "Unique identifier for the node"},
                "data": {"type": "object", "description": "Node properties matching the entity schema"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "entity_type", "entity_id", "data"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "get_graph_node",
        "title": "Get Graph Node",
        "description": "Get a specific node by its entity_id from a deployed graph project. Returns all node properties including created_at and updated_at timestamps.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "entity_type": {"type": "string", "description": "Entity key (e.g., 'person', 'concept')"},
                "entity_id": {"type": "string", "description": "The node's entity_id"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "entity_type", "entity_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "list_graph_nodes",
        "title": "List Graph Nodes",
        "description": "List nodes of a specific entity type from a deployed graph project. Supports pagination with limit/offset. Returns nodes ordered by creation date (newest first).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "entity_type": {"type": "string", "description": "Entity key (e.g., 'person', 'concept')"},
                "limit": {"type": "integer", "description": "Max results (default: 100, max: 1000)"},
                "offset": {"type": "integer", "description": "Pagination offset (default: 0)"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "entity_type"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "update_graph_node",
        "title": "Update Graph Node",
        "description": "Update properties of an existing node in a deployed graph project. Only send the fields you want to change — unspecified fields remain unchanged.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "entity_type": {"type": "string", "description": "Entity key (e.g., 'person', 'concept')"},
                "entity_id": {"type": "string", "description": "The node's entity_id"},
                "data": {"type": "object", "description": "Properties to update (partial update)"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "entity_type", "entity_id", "data"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "delete_graph_node",
        "title": "Delete Graph Node",
        "description": "Delete a node and all its relationships from a deployed graph project. ⚠️ This also removes all relationships connected to this node (DETACH DELETE).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "entity_type": {"type": "string", "description": "Entity key (e.g., 'person', 'concept')"},
                "entity_id": {"type": "string", "description": "The node's entity_id"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "entity_type", "entity_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
    },
    # ========================================================================
    # RELATIONSHIP OPERATIONS
    # ========================================================================
    {
        "name": "create_graph_relationship",
        "title": "Create Graph Relationship",
        "description": """Create a relationship between two nodes in a deployed graph project.

The rel_type must match a relationship key from the project schema.
Use get_graph_data_schema to see available relationship types.

Example:
  rel_type: "authored"
  from_id: "alan-turing-001"
  to_id: "on-computable-numbers-001"
  data: {"year": 1936}

The from_id and to_id must be entity_ids of existing nodes.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "rel_type": {"type": "string", "description": "Relationship key (e.g., 'authored', 'related_to')"},
                "from_id": {"type": "string", "description": "Source node entity_id"},
                "to_id": {"type": "string", "description": "Target node entity_id"},
                "data": {"type": "object", "description": "Relationship properties (optional)"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "rel_type", "from_id", "to_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "get_node_relationships",
        "title": "Get Node Relationships",
        "description": "Get all relationships connected to a specific node. Supports direction filtering (incoming, outgoing, both) and relationship type filtering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "entity_type": {"type": "string", "description": "Entity key of the node"},
                "entity_id": {"type": "string", "description": "The node's entity_id"},
                "direction": {"type": "string", "description": "Filter: incoming, outgoing, or both (default: both)"},
                "rel_type_filter": {"type": "string", "description": "Filter by relationship type (UPPER_SNAKE_CASE)"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "entity_type", "entity_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "delete_graph_relationship",
        "title": "Delete Graph Relationship",
        "description": "Delete a specific relationship by its internal ID. Use get_node_relationships to find relationship IDs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "rel_type": {"type": "string", "description": "Relationship key"},
                "rel_id": {"type": "integer", "description": "Internal relationship ID (from get_node_relationships)"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "rel_type", "rel_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
    },
    # ========================================================================
    # BULK OPERATIONS
    # ========================================================================
    {
        "name": "bulk_create_graph_nodes",
        "title": "Bulk Create Graph Nodes",
        "description": """Create multiple nodes at once (up to 500 per call). Uses Neo4j UNWIND for high performance.

Essential for knowledge graph population — create hundreds of entities from a single book chapter or article.

Each node needs: entity_id (unique string) and data (properties dict).

Example:
  entity_type: "concept"
  nodes: [
    {"entity_id": "quantum-mechanics-001", "data": {"name": "Quantum Mechanics", "field": "Physics"}},
    {"entity_id": "wave-function-001", "data": {"name": "Wave Function", "field": "Physics"}},
    {"entity_id": "superposition-001", "data": {"name": "Superposition", "field": "Physics"}}
  ]""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "entity_type": {"type": "string", "description": "Entity key for all nodes"},
                "nodes": {
                    "type": "array",
                    "description": "List of nodes. Each: {entity_id: string, data: {properties}}",
                    "items": {
                        "type": "object",
                        "properties": {
                            "entity_id": {"type": "string"},
                            "data": {"type": "object"}
                        },
                        "required": ["entity_id", "data"]
                    }
                },
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "entity_type", "nodes"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "bulk_create_graph_relationships",
        "title": "Bulk Create Graph Relationships",
        "description": """Create multiple relationships at once (up to 500 per call). Uses Neo4j UNWIND for high performance.

Essential for connecting knowledge — link hundreds of concepts, people, and events in one operation.

Each relationship needs: from_id, to_id, and optional data (properties).

Example:
  rel_type: "related_to"
  relationships: [
    {"from_id": "quantum-mechanics-001", "to_id": "wave-function-001", "data": {"strength": "strong"}},
    {"from_id": "quantum-mechanics-001", "to_id": "superposition-001", "data": {"strength": "strong"}}
  ]""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "rel_type": {"type": "string", "description": "Relationship key for all relationships"},
                "relationships": {
                    "type": "array",
                    "description": "List of relationships. Each: {from_id, to_id, data?}",
                    "items": {
                        "type": "object",
                        "properties": {
                            "from_id": {"type": "string"},
                            "to_id": {"type": "string"},
                            "data": {"type": "object"}
                        },
                        "required": ["from_id", "to_id"]
                    }
                },
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "rel_type", "relationships"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    # ========================================================================
    # SEARCH & QUERY
    # ========================================================================
    {
        "name": "search_graph_nodes",
        "title": "Search Graph Nodes",
        "description": """Search for nodes by property values in a deployed graph project.

Supports exact match and contains search (prefix value with ~ for contains).

Examples:
  Exact: filters: {"name": "Alan Turing"}
  Contains: filters: {"name": "~turing"} (case-insensitive)
  Combined: entity_type: "person", filters: {"field": "~physics"}

Without entity_type, searches ALL node types.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "entity_type": {"type": "string", "description": "Entity key to filter by (optional — omit to search all types)"},
                "filters": {"type": "object", "description": "Property filters. Prefix value with ~ for contains search."},
                "limit": {"type": "integer", "description": "Max results (default: 100, max: 1000)"},
                "offset": {"type": "integer", "description": "Pagination offset (default: 0)"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "filters"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "fulltext_search_graph",
        "title": "Full-Text Search Graph",
        "description": """Search across ALL string properties of ALL nodes in a deployed graph using free-text queries.

Unlike search_graph_nodes (which filters by specific property), this searches every text field at once.
Perfect for finding knowledge when you don't know which property contains the answer.

Example: query "quantum" searches name, description, summary, notes, and all other string fields.
Returns nodes with _match_fields showing which properties matched.

Optionally filter by entity_type to narrow results.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "query": {"type": "string", "description": "Search text (case-insensitive, min 2 chars)"},
                "entity_type": {"type": "string", "description": "Entity key to filter by (optional — omit to search all types)"},
                "limit": {"type": "integer", "description": "Max results (default: 50, max: 500)"},
                "offset": {"type": "integer", "description": "Pagination offset (default: 0)"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "query"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "traverse_graph",
        "title": "Traverse Graph",
        "description": """Walk the graph from a starting node, discovering connected knowledge.

Returns all nodes reachable within max_depth hops, with their distance from the start.
Essential for exploring knowledge graphs — find related concepts, trace connections, discover clusters.

Example: Start from "Alan Turing", traverse outgoing relationships up to 3 hops deep:
  start_entity_type: "person"
  start_entity_id: "alan-turing-001"
  max_depth: 3
  direction: "outgoing"

Supports filtering by relationship types and direction.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "start_entity_type": {"type": "string", "description": "Entity key of the starting node"},
                "start_entity_id": {"type": "string", "description": "Entity ID of the starting node"},
                "max_depth": {"type": "integer", "description": "Maximum traversal depth (default: 3, max: 10)"},
                "relationship_types": {
                    "type": "array",
                    "description": "Filter by relationship types (UPPER_SNAKE_CASE). Omit for all types.",
                    "items": {"type": "string"}
                },
                "direction": {"type": "string", "description": "Direction: outgoing, incoming, or both (default: both)"},
                "limit": {"type": "integer", "description": "Max results (default: 100, max: 1000)"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "start_entity_type", "start_entity_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    # ========================================================================
    # STATISTICS & INTROSPECTION
    # ========================================================================
    {
        "name": "get_graph_statistics",
        "title": "Get Graph Statistics",
        "description": "Get statistics about a deployed graph: total node count, total relationship count, counts per entity type, counts per relationship type. Essential for understanding the current state of a knowledge graph before adding more data.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "get_graph_data_schema",
        "title": "Get Graph Data Schema",
        "description": """Get the runtime schema of a DEPLOYED graph project — shows the actual entity types and relationship types available for data operations.

Returns: Available entity keys (for create_graph_node, list_graph_nodes, etc.) and relationship keys (for create_graph_relationship, etc.).

⭐ USE THIS FIRST before creating nodes/relationships to know what entity_type and rel_type values are valid.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
]


# ============================================================================
# MODULE TOOLS (a project's own frontends and backends)
# ============================================================================
# A module is a frontend or backend built from your GitHub repository and run beside the project's API
# on its resource pool. Each operation goes through the studio's own module route, and the ones that
# build or restart a module are jobs (get_job_status). A variable's value never comes back.

MODULE_TOOLS = [
    {
        "name": "list_modules",
        "title": "List Modules",
        "description": "List a project's modules and what each runs: module_id (what every module tool takes), name, type (frontblok or logicblok), repository, url, staging_status (not_deployed, deploying, deployed, failed), deployed_at, image (the image of its last successful build, named by the commit it built: <name>:<short sha>-<build time>), replicas (live pods: 0 when frozen, null while the pool is not reporting), CPU and memory, and env_var_names (the names of its environment variables, never their values).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "deploy_module",
        "title": "Deploy Module",
        "description": "Deploy a new module from a GitHub repository onto the project's resource pool: a frontblok module is a Vite frontend, a logicblok module a backend built from its Dockerfile that serves port 8000 with GET /health. Its job clones the repository (the default branch head, or git_ref), builds it and serves it at the module_url the answer names; the project's CORS origins take the module in. A private repository needs the RationalBloks GitHub App installed on it. The operation is ASYNCHRONOUS: poll the returned job_id with get_job_status." + PLATFORM_UPDATE_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID) the module belongs to"},
                "module_name": {"type": "string", "description": "Display name"},
                "github_repo_url": {"type": "string", "description": "https://github.com/<owner>/<repo>"},
                "module_type": {"type": "string", "enum": ["frontblok", "logicblok"], "description": "frontblok (a Vite frontend) or logicblok (a backend built from its Dockerfile)"},
                "dockerfile_path": {"type": "string", "description": "Dockerfile path inside the repository (default: Dockerfile)"},
                "cpu_millicores": {"type": "integer", "description": "CPU allocation (default: 100)"},
                "memory_mb": {"type": "integer", "description": "Memory allocation (default: 128)"},
                "env_vars": {"type": "object", "additionalProperties": {"type": "string"},
                             "description": "Environment variables {NAME: value}, each value text"},
                "git_ref": {"type": "string", "description": "Branch, tag or commit SHA for this first build (default: the default branch head)"}
            },
            "required": ["project_id", "module_name", "github_repo_url", "module_type"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "redeploy_module",
        "title": "Redeploy Module",
        "description": "Rebuild a module from its repository's default branch head and roll it out, keeping its pod count. Its data and settings are untouched; the project's API (staging and production) and its backend modules restart to take the module's CORS origin. The operation is ASYNCHRONOUS: poll the returned job_id with get_job_status, whose result names the image built (its commit); list_modules shows it once done." + BUSY_MODULE_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "module_id": {"type": "string", "description": "Module ID (list_modules)"}
            },
            "required": ["module_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "update_module",
        "title": "Update Module",
        "description": "Rename a module, or point it at another GitHub repository, which its next redeploy builds. Pass module_name, github_repo_url or both." + BUSY_MODULE_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "module_id": {"type": "string", "description": "Module ID (list_modules)"},
                "module_name": {"type": "string", "description": "New display name"},
                "github_repo_url": {"type": "string", "description": "New repository, https://github.com/<owner>/<repo>"}
            },
            "required": ["module_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "delete_module",
        "title": "Delete Module",
        "description": "Remove a module: its pods stop and it leaves the project and its CORS origins. DESTRUCTIVE." + BUSY_MODULE_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "module_id": {"type": "string", "description": "Module ID (list_modules)"}
            },
            "required": ["module_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "set_module_env",
        "title": "Set Module Environment",
        "description": "Set a module's environment variables: {NAME: value} sets one, {NAME: null} removes one, and every variable not named is kept. A backend module restarts to take them; a frontend module rebuilds (they are build arguments). Values are stored encrypted and never returned: the answer and list_modules name the variables only. DESTRUCTIVE: a value replaced or removed cannot be read back. CORS_ORIGINS, DEPLOY_* and GITHUB_TOKEN are the platform's. The operation is a job: poll the returned job_id with get_job_status." + BUSY_MODULE_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "module_id": {"type": "string", "description": "Module ID (list_modules)"},
                "env_vars": {"type": "object", "additionalProperties": {"type": ["string", "null"]},
                             "description": "{NAME: value} to set (text), {NAME: null} to remove; variables not named are kept"}
            },
            "required": ["module_id", "env_vars"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}
    },
    {
        "name": "freeze_module",
        "title": "Freeze Module",
        "description": "Stop a module's pods (scale to 0), remembering how many it ran; unfreeze_module starts them again. Freezing a frozen module changes nothing." + BUSY_MODULE_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "module_id": {"type": "string", "description": "Module ID (list_modules)"}
            },
            "required": ["module_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "unfreeze_module",
        "title": "Unfreeze Module",
        "description": "Start a frozen module's pods again, as many as it ran before the freeze. A running module is left as it is." + BUSY_MODULE_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "module_id": {"type": "string", "description": "Module ID (list_modules)"}
            },
            "required": ["module_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "scale_module",
        "title": "Scale Module",
        "description": "Run 1 or 2 pods of a module (freeze_module stops it)." + BUSY_MODULE_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "module_id": {"type": "string", "description": "Module ID (list_modules)"},
                "replicas": {"type": "integer", "enum": [1, 2], "description": "1 or 2 pods"}
            },
            "required": ["module_id", "replicas"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "set_module_resources",
        "title": "Set Module Resources",
        "description": "Set a module's CPU and memory and rebuild it so its pods take them. The allocation is checked against the resource pool's capacity first; a refused one is restored. The operation is ASYNCHRONOUS: poll the returned job_id with get_job_status." + BUSY_MODULE_REFUSAL,
        "inputSchema": {
            "type": "object",
            "properties": {
                "module_id": {"type": "string", "description": "Module ID (list_modules)"},
                "cpu_millicores": {"type": "integer", "description": "CPU allocation in millicores"},
                "memory_mb": {"type": "integer", "description": "Memory allocation in MB"}
            },
            "required": ["module_id", "cpu_millicores", "memory_mb"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
    },
]


# ============================================================================
# BACKEND PROMPTS
# ============================================================================

BACKEND_PROMPTS = [
    Prompt(
        name="create-project-from-description",
        title="Create Project from Description",
        description="Generate a complete RationalBloks project schema from a plain English description",
        arguments=[
            PromptArgument(
                name="description",
                description="Plain English description of the data model you want to create",
                required=True,
            )
        ],
    ),
    Prompt(
        name="fix-schema-errors",
        title="Fix Schema Errors",
        description="Analyze and fix common schema format errors",
        arguments=[
            PromptArgument(
                name="schema",
                description="The JSON schema that is causing errors",
                required=True,
            ),
            PromptArgument(
                name="error_message",
                description="The error message you received",
                required=False,
            ),
        ],
    ),
]


# ============================================================================
# GRAPH PROMPTS
# ============================================================================

GRAPH_PROMPTS = [
    Prompt(
        name="create-graph-project-from-description",
        title="Create Graph Project from Description",
        description="Generate a complete RationalBloks graph project schema from a plain English description",
        arguments=[
            PromptArgument(
                name="description",
                description="Plain English description of the graph data model you want to create",
                required=True,
            )
        ],
    ),
]


# ============================================================================
# BACKEND MCP SERVER
# ============================================================================

# Every tool the server offers
INFRASTRUCTURE_TOOLS = BACKEND_TOOLS + GRAPH_TOOLS + GRAPH_DATA_TOOLS + MODULE_TOOLS

# The lists under the titles the API reference resource gives them
TOOL_GROUPS = (
    ("Relational Tools", BACKEND_TOOLS),
    ("Graph Schema Tools", GRAPH_TOOLS),
    ("Graph Data Tools", GRAPH_DATA_TOOLS),
    ("Module Tools", MODULE_TOOLS),
)


def _kind(tool: dict) -> str:
    # A tool's kind as its annotations declare it: Read, Write (never loses data) or Destructive
    hints = tool["annotations"]
    if hints["readOnlyHint"]:
        return "Read"
    return "Destructive" if hints["destructiveHint"] else "Write"


def api_reference() -> str:
    # The rationalbloks://docs/api-reference resource, written from the tool lists themselves, so it names
    # exactly the tools the server serves, each under the kind its annotations declare
    lines = ["# RationalBloks MCP API Reference", "",
             "Read tools only read. Write tools never lose data. Destructive tools can, and declare destructiveHint."]
    for title, tools in TOOL_GROUPS:
        lines += ["", f"## {title}"]
        for kind in ("Read", "Write", "Destructive"):
            names = [tool["name"] for tool in tools if _kind(tool) == kind]
            if names:
                lines.append(f"- {kind}: {', '.join(names)}")
    lines += ["", "For full documentation, visit https://rationalbloks.com/documentation"]
    return "\n".join(lines) + "\n"


class BackendMCPServer(BaseMCPServer):
    # Backend MCP server: every tool a pass-through to LogicBlok's gateway, the prompts, and a tool list
    # narrowed to what the request's key may call

    # Sent to every client on connect. Claude Code keeps the first 2048 characters of a server's
    # instructions, so they stay under that, the rule that keeps data safe first.
    INSTRUCTIONS = """RationalBloks: production REST APIs (PostgreSQL) and graph APIs (Neo4j) generated from JSON schemas and deployed onto your own resource pools.

CHANGE A SCHEMA SAFELY
1. get_schema (tables/fields for a slice; its version pins the save)
2. preview_schema_change: the diff and the deploy plan, nothing saved
3. patch_schema (add, rename, set; never drops), drop_schema_items (drops) or update_schema (the whole schema)
4. deploy_staging, then get_job_status until completed or failed
A deploy tool refuses a plan that drops data and names the drops; deploy_destructive applies it once the drops are confirmed intended. deploy_production promotes staging.

REBUILD WITHOUT A SCHEMA CHANGE: redeploy_project (staging); deploy_production when staging runs what production runs.

MODULES (your frontends and backends, built from GitHub): list_modules, deploy_module, redeploy_module, set_module_env (values are write-only), freeze_module, unfreeze_module, scale_module, set_module_resources, update_module, delete_module.

JOBS: deploys, promotions, rollbacks, deletions and module builds are jobs; list_project_jobs finds a lost job_id. A failed job's failure_side says whether the project's input caused it.

START: list_projects; create_project needs a cluster_id from list_clusters; get_template_schemas shows valid schemas, get_schema_reference the advanced features (__policy__, computed columns, __constraints__, deletes with a stated count).

RELATIONAL: FLAT {"table": {"field": {"type": ...}}}; a string has max_length; "datetime", not "timestamp"; never define id, created_at, updated_at; users are the built-in app_users (foreign_key "app_users.id").
GRAPH: {"nodes": {...}, "relationships": {...}}; PascalCase entities, UPPER_SNAKE_CASE relationships.

Setup and Claude Code permissions: https://rationalbloks.com/documentation"""

    def __init__(
        self,
        api_key: str | None = None,
        http_mode: bool = False,
    ) -> None:
        # Initialize backend MCP server
        super().__init__(
            name="rationalbloks-backend",
            version=__version__,
            instructions=self.INSTRUCTIONS,
            api_key=api_key,
            http_mode=http_mode,
        )

        # Register infrastructure tools, prompts and the API reference written from the tools
        self.register_tools(INFRASTRUCTURE_TOOLS)
        self.register_prompts(BACKEND_PROMPTS)
        self.register_prompts(GRAPH_PROMPTS)
        self.register_resource("rationalbloks://docs/api-reference", api_reference())

        # Register tool handler, and the tool list's narrowing to the request's key
        self.register_tool_handler("*", self._handle_backend_tool)
        self.register_tool_filter(self._allowed_tools)

        # Register prompt handlers
        self.register_prompt_handler(
            "create-project-from-description",
            self._handle_create_project_prompt,
        )
        self.register_prompt_handler(
            "fix-schema-errors",
            self._handle_fix_schema_prompt,
        )
        self.register_prompt_handler(
            "create-graph-project-from-description",
            self._handle_create_graph_project_prompt,
        )

    def _get_client(self) -> LogicBlokClient:
        # A LogicBlok client for the request's API key
        api_key = self.get_api_key_for_request()
        if not api_key:
            raise ValueError("No RationalBloks API key: set RATIONALBLOKS_API_KEY (a local server) or send the header "
                             "Authorization: Bearer rb_sk_... (the hosted server). Create one at "
                             "https://rationalbloks.com/settings")
        return LogicBlokClient(api_key)

    async def _handle_backend_tool(self, name: str, arguments: dict) -> Any:
        # Single dispatch: every tool is a passthrough to LogicBlok's /api/mcp/execute endpoint.
        # LogicBlok is the source of truth for tool semantics, argument validation and error messages.
        async with self._get_client() as client:
            return await client.execute(name, arguments)

    async def _allowed_tools(self) -> set | None:
        # The tools the request's key may call (GET /api/mcp/allowed-tools): a read-only key's server lists
        # the read tools alone, so a client allows all of it with one rule. None for a request without a
        # key, which is shown every tool, since it can call none of them (a directory reading the server).
        if not self.get_api_key_for_request():
            return None
        async with self._get_client() as client:
            return set(await client.allowed_tools())

    def _handle_create_project_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        # Handle create-project-from-description prompt
        description = arguments.get("description", "") if arguments else ""

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Create a RationalBloks project schema for: {description}

═══════════════════════════════════════════════════════════════════════════
CRITICAL SCHEMA RULES - FOLLOW EXACTLY:
═══════════════════════════════════════════════════════════════════════════

1. FLAT FORMAT (REQUIRED):
   ✅ CORRECT: {{"users": {{"email": {{"type": "string", "max_length": 255}}}}}}
   ❌ WRONG: {{"users": {{"fields": {{"email": {{"type": "string"}}}}}}}}
   DO NOT nest under 'fields' key!

2. FIELD TYPE REQUIREMENTS:
   • string: MUST have "max_length" (e.g., "max_length": 255)
   • decimal: MUST have "precision" and "scale" (e.g., "precision": 10, "scale": 2)
   • datetime: Use "datetime" NOT "timestamp"
   • ALL fields: MUST have "type" property

3. AUTOMATIC FIELDS (DON'T define):
   • id (uuid, primary key)
   • created_at (datetime)
   • updated_at (datetime)

4. USER AUTHENTICATION:
   ❌ NEVER create "users", "customers", "employees", "members" tables
   ✅ USE built-in app_users table

   Example:
   {{
     "employee_profiles": {{
       "user_id": {{"type": "uuid", "foreign_key": "app_users.id", "required": true}},
       "department": {{"type": "string", "max_length": 100}}
     }}
   }}

5. AUTHORIZATION (user ownership):
   • Add user_id foreign key to app_users.id for user-owned resources

   Example:
   {{
     "orders": {{
       "user_id": {{"type": "uuid", "foreign_key": "app_users.id"}},
       "total": {{"type": "decimal", "precision": 10, "scale": 2}}
     }}
   }}

6. FIELD OPTIONS:
   • required: true/false
   • unique: true/false
   • default: any value
   • enum: ["value1", "value2"]
   • foreign_key: "table_name.id"

AVAILABLE TYPES: string, text, integer, decimal, boolean, uuid, date, datetime, json, uuid_array, integer_array, text_array, float_array

   Array types store PostgreSQL native arrays with automatic GIN indexing:
   • uuid_array: UUID[] — for sets of references (e.g., tensor coordinates)
   • integer_array: BIGINT[] — for dimension indices, integer sets
   • text_array: TEXT[] — for tags, categories, label sets
   • float_array: DOUBLE PRECISION[] — for weight vectors, scores

═══════════════════════════════════════════════════════════════════════════

Generate the schema now following ALL rules above:""",
                    ),
                )
            ]
        )

    def _handle_fix_schema_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        # Handle fix-schema-errors prompt
        schema = arguments.get("schema", "{}") if arguments else "{}"
        error = arguments.get("error_message", "Unknown error") if arguments else "Unknown error"

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Fix this RationalBloks schema:

Schema:
{schema}

Error: {error}

═══════════════════════════════════════════════════════════════════════════
COMMON SCHEMA ERRORS:
═══════════════════════════════════════════════════════════════════════════

1. NESTED 'fields' KEY:
   ❌ {{"users": {{"fields": {{"email": {{...}}}}}}}}
   ✅ {{"users": {{"email": {{...}}}}}}

2. MISSING TYPE PROPERTY:
   ❌ {{"name": {{"required": true}}}}
   ✅ {{"name": {{"type": "string", "max_length": 100, "required": true}}}}

3. STRING WITHOUT max_length:
   ❌ {{"email": {{"type": "string"}}}}
   ✅ {{"email": {{"type": "string", "max_length": 255}}}}

4. DECIMAL WITHOUT precision/scale:
   ❌ {{"price": {{"type": "decimal"}}}}
   ✅ {{"price": {{"type": "decimal", "precision": 10, "scale": 2}}}}

5. USING "timestamp" INSTEAD OF "datetime":
   ❌ {{"created": {{"type": "timestamp"}}}}
   ✅ {{"created": {{"type": "datetime"}}}}

6. DEFINING AUTOMATIC FIELDS:
   ❌ {{"id": {{...}}}}, {{"created_at": {{...}}}}, {{"updated_at": {{...}}}}
   ✅ Don't define these - they're automatic

7. CREATING users/customers/employees TABLE:
   ❌ {{"users": {{"email": {{...}}, "password": {{...}}}}}}
   ✅ Use app_users pattern with foreign key

CHECK ALL THESE ISSUES and provide the corrected schema:""",
                    ),
                )
            ]
        )

    def _handle_create_graph_project_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        # Handle create-graph-project-from-description prompt
        description = arguments.get("description", "") if arguments else ""

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Create a RationalBloks graph project schema for: {description}

═══════════════════════════════════════════════════════════════════════════
GRAPH SCHEMA FORMAT — FOLLOW EXACTLY:
═══════════════════════════════════════════════════════════════════════════

Graph schemas define nodes (entities) and relationships — NOT flat database tables.
Each field is a dict with "type" and optional "required": true (defaults to false).

STRUCTURE:
{{
  "nodes": {{
    "EntityName": {{
      "description": "What this entity represents",
      "flat_labels": ["AdditionalLabel"],
      "schema": {{
        "field_name": {{"type": "string", "required": true}},
        "other_field": {{"type": "integer"}}
      }}
    }}
  }},
  "relationships": {{
    "RELATIONSHIP_TYPE": {{
      "from": "EntityName",
      "to": "OtherEntity",
      "cardinality": "MANY_TO_MANY",
      "data_schema": {{
        "field_name": {{"type": "date"}}
      }}
    }}
  }}
}}

FIELD TYPES: string, integer, float, boolean, date, json

CARDINALITY: ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY

RULES:
1. "nodes" key is REQUIRED — must contain at least one entity
2. Each entity needs "description" and "schema" with field definitions
3. Each field is {{"type": "...", "required": true/false}} — required defaults to false
4. Relationship "from"/"to" must reference defined node names
5. Relationship types: UPPER_SNAKE_CASE (e.g., FOLLOWS, CREATED_BY)
6. Entity names: PascalCase (e.g., Person, Product)
7. Nest entities inside parents to create type hierarchies
8. Automatic fields (id, created_at, updated_at) are NOT needed

HIERARCHICAL EXAMPLE:
{{
  "nodes": {{
    "Vehicle": {{
      "description": "A vehicle",
      "flat_labels": ["Transport"],
      "schema": {{
        "make": {{"type": "string", "required": true}},
        "model": {{"type": "string", "required": true}},
        "year": {{"type": "integer"}}
      }},
      "Car": {{
        "description": "A car (inherits Vehicle labels)",
        "flat_labels": ["Automobile"],
        "schema": {{
          "doors": {{"type": "integer", "required": true}},
          "electric": {{"type": "boolean"}}
        }}
      }}
    }}
  }}
}}

Generate the graph schema now following ALL rules above:""",
                    ),
                )
            ]
        )


def create_backend_server(
    api_key: str | None = None,
    http_mode: bool = False,
) -> BackendMCPServer:
    # Factory function to create a backend MCP server
    # Returns: Configured BackendMCPServer instance
    return BackendMCPServer(api_key=api_key, http_mode=http_mode)
