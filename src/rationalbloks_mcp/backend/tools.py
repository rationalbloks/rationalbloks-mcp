# ============================================================================
# RATIONALBLOKS MCP - BACKEND TOOLS
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# 29 Backend tools (18 relational + 11 graph):
#
# RELATIONAL (18):
#   READ (11): list_projects, get_project, get_schema, get_user_info,
#              get_job_status, get_project_info, get_version_history,
#              get_template_schemas, get_subscription_status, get_project_usage,
#              get_schema_at_version
#   WRITE (7): create_project, update_schema, deploy_staging, deploy_production,
#              delete_project, rollback_project, rename_project
#
# GRAPH (11):
#   READ (5):  get_graph_schema, get_graph_template_schemas,
#              get_graph_version_history, get_graph_schema_at_version,
#              get_graph_project_info
#   WRITE (6): create_graph_project, update_graph_schema,
#              deploy_graph_staging, deploy_graph_production,
#              delete_graph_project, rollback_graph_project
# ============================================================================

import os
import sys
from typing import Any

from mcp.types import Prompt, PromptArgument, PromptMessage, GetPromptResult, TextContent

from .. import __version__
from ..core import BaseMCPServer
from .client import LogicBlokClient

# Public API
__all__ = [
    "BACKEND_TOOLS",
    "BackendMCPServer",
    "create_backend_server",
]


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

BACKEND_TOOLS = [
    # --- READ OPERATIONS ---
    {
        "name": "list_projects",
        "title": "List Projects",
        "description": "List all your RationalBloks projects with their status and URLs",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
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
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
    },
    {
        "name": "get_schema",
        "title": "Get Project Schema",
        "description": "Get the JSON schema definition of a project in FLAT format. Returns the schema structure where each table name maps directly to field definitions. This is the same format required for create_project and update_schema. USE CASES: Review current schema before making updates, copy schema as template for new projects, verify schema structure after deployment, learn the correct schema format by example. The returned schema will be in FLAT format: {table_name: {field_name: {type, properties}}}",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
    },
    {
        "name": "get_user_info",
        "title": "Get User Info",
        "description": "Get information about the authenticated user",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
    },
    {
        "name": "get_job_status",
        "title": "Get Job Status",
        "description": "Check the status of a deployment job. STATUS VALUES: pending (job queued), running (deployment in progress), completed (success), failed (deployment failed). TIMELINE: Typical deployment takes 2-5 minutes. If status is 'running' for >10 minutes, check get_project_info for detailed pod status. If status is 'failed', use get_project_info to see deployment errors and check schema format (must be FLAT, no 'fields' nesting).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Job ID returned from deployment operations"}
            },
            "required": ["job_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
    },
    {
        "name": "get_project_info",
        "title": "Get Project Info",
        "description": "Get detailed project info including deployment status and resource usage. DEPLOYMENT STATUS: Running (healthy), Pending (starting), CrashLoopBackOff (init container failed - usually schema format error), ImagePullBackOff (image build failed). TROUBLESHOOTING: If status is CrashLoopBackOff, the schema is likely in wrong format (nested 'fields' key or missing 'type' properties). Use get_schema to review current schema. If replicas show 0/2, the init container (migration runner) is failing. This is almost always a schema format issue.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
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
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
    },
    {
        "name": "get_template_schemas",
        "title": "Get Template Schemas",
        "description": "Get pre-built template schemas for common use cases. ⭐ USE THIS FIRST when creating a new project! Templates show the CORRECT schema format with: proper FLAT structure (no 'fields' nesting), every field has a 'type' property, foreign key relationships configured correctly, best practices for field naming and types. Available templates: E-commerce (products, orders, customers), Team collaboration (projects, tasks, users), General purpose templates. You can use these templates directly with create_project or modify them for your needs. TIP: Study these templates to understand the correct schema format before creating custom schemas.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
    },
    {
        "name": "get_subscription_status",
        "title": "Get Subscription Status",
        "description": "Get your subscription tier, limits, and usage",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
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
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
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
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}
    },
    {
        "name": "create_project",
        "title": "Create Project",
        "description": """Create a new RationalBloks project from a JSON schema.

⚠️ CRITICAL RULES - READ BEFORE CREATING SCHEMA:

1. FLAT FORMAT (REQUIRED):
   ✅ CORRECT: {users: {email: {type: "string", max_length: 255}}}
   ❌ WRONG: {users: {fields: {email: {type: "string"}}}}
   DO NOT nest under 'fields' key!

2. FIELD TYPE REQUIREMENTS:
   • string: MUST have "max_length" (e.g., max_length: 255)
   • decimal: MUST have "precision" and "scale" (e.g., precision: 10, scale: 2)
   • datetime: Use "datetime" NOT "timestamp"
   • ALL fields: MUST have "type" property

3. AUTOMATIC FIELDS (DON'T define):
   • id (uuid, primary key)
   • created_at (datetime)
   • updated_at (datetime)

4. USER AUTHENTICATION:
   ❌ NEVER create "users", "customers", "employees" tables with email/password
   ✅ USE built-in app_users table
   
   Example:
   {
     "employee_profiles": {
       "user_id": {type: "uuid", foreign_key: "app_users.id", required: true},
       "department": {type: "string", max_length: 100}
     }
   }

5. AUTHORIZATION:
   Add user_id → app_users.id to enable "only see your own data"
   
   Example:
   {
     "orders": {
       "user_id": {type: "uuid", foreign_key: "app_users.id"},
       "total": {type: "decimal", precision: 10, scale: 2}
     }
   }

6. FIELD OPTIONS:
   • required: true/false
   • unique: true/false
   • default: any value
   • enum: ["val1", "val2"]
   • foreign_key: "table.id"

AVAILABLE TYPES: string, text, integer, decimal, boolean, uuid, date, datetime, json

WORKFLOW:
1. Use get_template_schemas FIRST to see valid examples
2. Create schema following ALL rules above
3. Call this tool
4. Monitor with get_job_status (2-5 min deployment)

After creation, use get_job_status with returned job_id to monitor deployment.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name"},
                "schema": {"type": "object", "description": "JSON schema in FLAT format (table_name → field_name → properties). Every field MUST have a 'type' property. Use get_template_schemas to see valid examples."},
                "description": {"type": "string", "description": "Optional project description"}
            },
            "required": ["name", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
    },
    {
        "name": "update_schema",
        "title": "Update Schema",
        "description": """Update a project's schema (saves to database, does NOT deploy).

⚠️ CRITICAL: Follow ALL rules from create_project:
• FLAT format (no 'fields' nesting)
• string: MUST have max_length
• decimal: MUST have precision + scale
• Use "datetime" NOT "timestamp"
• DON'T define: id, created_at, updated_at
• NEVER create users/customers/employees tables (use app_users)

⚠️ MIGRATION RULES:
• New fields MUST be "required": false OR have "default" value
• Cannot add required field without default to existing tables
• Safe: {new_field: {type: "string", max_length: 100, required: false}}

WORKFLOW:
1. Use get_schema to see current schema
2. Modify following ALL rules
3. Call update_schema (saves only)
4. Call deploy_staging to apply changes
5. Monitor with get_job_status

NOTE: This only saves the schema. You MUST call deploy_staging afterwards to apply changes.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "schema": {"type": "object", "description": "New JSON schema in FLAT format (table_name → field_name → properties). Every field MUST have a 'type' property."}
            },
            "required": ["project_id", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True}
    },
    {
        "name": "deploy_staging",
        "title": "Deploy to Staging",
        "description": "Deploy a project to the staging environment. This triggers: (1) Schema validation, (2) Docker image build, (3) GitHub commit, (4) Kubernetes deployment, (5) Database migrations. The operation is ASYNCHRONOUS - it returns immediately with a job_id. Use get_job_status with the job_id to monitor progress. Deployment typically takes 2-5 minutes depending on schema complexity. If deployment fails, check: (1) Schema format is FLAT (no 'fields' nesting), (2) Every field has a 'type' property, (3) Foreign keys reference existing tables, (4) No PostgreSQL reserved words in table/field names. Use get_project_info to see if the deployment succeeded.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
    },
    {
        "name": "deploy_production",
        "title": "Deploy to Production",
        "description": "Promote staging to production (requires paid plan)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
    },
    {
        "name": "delete_project",
        "title": "Delete Project",
        "description": "Delete a project (removes GitHub repo, K8s deployments, and database)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True}
    },
    {
        "name": "rollback_project",
        "title": "Rollback Project",
        "description": "Rollback a project to a previous version. ⚠️ WARNING: This reverts schema AND code to the specified commit. Database data is NOT rolled back. Use get_version_history to find the commit SHA of the version you want to rollback to. After rollback, use get_job_status to monitor the redeployment. Rollback is useful when a schema change breaks deployment.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "version": {"type": "string", "description": "Commit SHA or version to rollback to"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "version"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True}
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
# GRAPH TOOLS (11 tools for Neo4j graph database projects)
# ============================================================================

GRAPH_TOOLS = [
    # ========================================================================
    # READ TOOLS
    # ========================================================================
    {
        "name": "get_graph_schema",
        "title": "Get Graph Schema",
        "description": "Get the graph schema definition of a project. Returns the hierarchical schema with nodes (entities) and relationships. Graph schemas define entity hierarchies and typed relationships — a different format than relational flat-table schemas.",
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
        "description": """Get pre-built graph template schemas for common use cases. ⭐ USE THIS FIRST when creating a new graph project! Templates show the CORRECT graph schema format with: proper node definitions (description, flat_labels, schema with required/optional fields), relationship configurations (from, to, cardinality, data_schema), and hierarchical entity nesting. Available templates: Social Network (users, posts, follows), Knowledge Graph (topics, articles, authors), Product Catalog (products, categories, suppliers). You can use these templates directly with create_graph_project or modify them for your needs. TIP: Study these templates to understand the correct graph schema format before creating custom schemas.""",
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

SCHEMA STRUCTURE:
{
  "nodes": {
    "EntityName": {
      "description": "What this entity represents",
      "flat_labels": ["AdditionalLabel"],
      "schema": {
        "required_fields": {"field_name": "type"},
        "optional_fields": {"field_name": "type"}
      }
    }
  },
  "relationships": {
    "RELATIONSHIP_TYPE": {
      "from": "EntityName",
      "to": "OtherEntity",
      "cardinality": "MANY_TO_MANY",
      "data_schema": {
        "required_fields": {"field_name": "type"},
        "optional_fields": {"field_name": "type"}
      }
    }
  }
}

FIELD TYPES: string, integer, float, boolean, date, json

CARDINALITY OPTIONS: ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY

HIERARCHICAL NODES:
Nest entities inside parent entities to create type hierarchies.
Child entities inherit parent labels automatically.

Example:
{
  "nodes": {
    "Animal": {
      "description": "Base animal entity",
      "flat_labels": ["LivingThing"],
      "schema": {
        "required_fields": {"name": "string"},
        "optional_fields": {"habitat": "string"}
      },
      "Dog": {
        "description": "A dog (inherits Animal labels)",
        "flat_labels": ["Pet"],
        "schema": {
          "required_fields": {"breed": "string"},
          "optional_fields": {"trained": "boolean"}
        }
      }
    }
  },
  "relationships": {
    "OWNS": {
      "from": "Person",
      "to": "Animal",
      "cardinality": "ONE_TO_MANY"
    }
  }
}

RULES:
1. "nodes" key is REQUIRED — must contain at least one entity
2. Each entity needs "description" and "schema" with required/optional fields
3. Relationship "from"/"to" must reference defined node names
4. Relationship types should be UPPER_SNAKE_CASE
5. Entity names should be PascalCase
6. Automatic fields (id, created_at, updated_at) are NOT needed
7. Use get_graph_template_schemas FIRST to see valid examples

WORKFLOW:
1. Use get_graph_template_schemas to see valid examples
2. Create schema following the rules above
3. Call this tool
4. Monitor with get_job_status (2-5 min deployment)

After creation, use get_job_status with returned job_id to monitor deployment.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Project name"},
                "schema": {"type": "object", "description": "Graph schema with 'nodes' and optionally 'relationships' keys. Use get_graph_template_schemas to see valid examples."},
                "description": {"type": "string", "description": "Optional project description"}
            },
            "required": ["name", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
    },
    {
        "name": "update_graph_schema",
        "title": "Update Graph Schema",
        "description": """Update a graph project's schema (saves to database, does NOT deploy).

⚠️ Follow ALL rules from create_graph_project:
• Must have "nodes" key with at least one entity
• Each entity needs "description" and "schema" with required/optional fields
• Relationships need "from", "to", and "cardinality"
• Field types: string, integer, float, boolean, date, json
• Relationship types should be UPPER_SNAKE_CASE
• Entity names should be PascalCase

WORKFLOW:
1. Use get_graph_schema to see current schema
2. Modify following all rules
3. Call update_graph_schema (saves only)
4. Call deploy_graph_staging to apply changes
5. Monitor with get_job_status

NOTE: This only saves the schema. You MUST call deploy_graph_staging afterwards to deploy.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "schema": {"type": "object", "description": "New graph schema with 'nodes' and optionally 'relationships' keys."}
            },
            "required": ["project_id", "schema"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True}
    },
    {
        "name": "deploy_graph_staging",
        "title": "Deploy Graph to Staging",
        "description": "Deploy a graph project to the staging environment. This triggers: (1) Schema validation, (2) Neo4j entity code generation, (3) Docker image build, (4) GitHub commit, (5) Kubernetes deployment with Neo4j instance. The operation is ASYNCHRONOUS — returns immediately with a job_id. Use get_job_status to monitor progress. Deployment typically takes 2-5 minutes. Use get_graph_project_info to verify deployment succeeded.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
    },
    {
        "name": "deploy_graph_production",
        "title": "Deploy Graph to Production",
        "description": "Promote graph staging to production. Creates a separate production Neo4j instance with its own credentials and database. Requires paid plan.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
    },
    {
        "name": "delete_graph_project",
        "title": "Delete Graph Project",
        "description": "Delete a graph project (removes GitHub repo, K8s deployments, Neo4j database, and credentials)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"}
            },
            "required": ["project_id"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True}
    },
    {
        "name": "rollback_graph_project",
        "title": "Rollback Graph Project",
        "description": "Rollback a graph project to a previous version. ⚠️ WARNING: This reverts schema AND code to the specified commit. Neo4j data is NOT rolled back. Use get_graph_version_history to find the commit SHA of the version you want to rollback to. After rollback, the graph API will be redeployed with the old schema.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project ID (UUID)"},
                "version": {"type": "string", "description": "Commit SHA to rollback to"},
                "environment": {"type": "string", "description": "Environment: staging or production (default: staging)"}
            },
            "required": ["project_id", "version"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True}
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

class BackendMCPServer(BaseMCPServer):
    # Backend MCP server with 29 tools (18 relational + 11 graph)
    # Extends BaseMCPServer with: LogicBlok client integration, backend + graph tools, prompts
    
    INSTRUCTIONS = """RationalBloks MCP Server — Backend Mode

Build production REST APIs and Graph APIs from JSON schemas in seconds.

═══════════════════════════════════════════════════════════════════════════
TWO PROJECT TYPES:
═══════════════════════════════════════════════════════════════════════════

1. RELATIONAL (PostgreSQL) — Flat table schemas, SQL databases, CRUD APIs
   Tools: create_project, get_schema, deploy_staging, etc. (18 tools)

2. GRAPH (Neo4j) — Hierarchical node/relationship schemas, graph databases
   Tools: create_graph_project, get_graph_schema, deploy_graph_staging, etc. (11 tools)

═══════════════════════════════════════════════════════════════════════════
RELATIONAL SCHEMA RULES:
═══════════════════════════════════════════════════════════════════════════

1. FLAT FORMAT: {"users": {"email": {"type": "string", "max_length": 255}}}
2. string: MUST have max_length | decimal: MUST have precision + scale
3. Use "datetime" NOT "timestamp"
4. DON'T define: id, created_at, updated_at (automatic)
5. NEVER create users/customers tables — use built-in app_users
6. Use get_template_schemas FIRST to see valid examples

═══════════════════════════════════════════════════════════════════════════
GRAPH SCHEMA RULES:
═══════════════════════════════════════════════════════════════════════════

1. HIERARCHICAL FORMAT with "nodes" and "relationships" keys
2. Field types: string, integer, float, boolean, date, json
3. Cardinality: ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY
4. Entity names: PascalCase | Relationship types: UPPER_SNAKE_CASE
5. Nest entities inside parents to create type hierarchies
6. Use get_graph_template_schemas FIRST to see valid examples

═══════════════════════════════════════════════════════════════════════════
SHARED TOOLS (work for both project types):
═══════════════════════════════════════════════════════════════════════════

list_projects, get_project, get_job_status, get_user_info,
get_subscription_status, rename_project

═══════════════════════════════════════════════════════════════════════════
WORKFLOW:
═══════════════════════════════════════════════════════════════════════════

1. Use get_template_schemas or get_graph_template_schemas for examples
2. Create schema following the appropriate rules
3. Call create_project or create_graph_project
4. Monitor with get_job_status (deployment takes 2-5 minutes)
5. Use get_project_info or get_graph_project_info to verify

Available: 29 tools (18 relational + 11 graph) for projects, schemas, and deployments.
Full documentation: https://infra.rationalbloks.com/documentation"""
    
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
        
        # Register backend tools and prompts
        self.register_tools(BACKEND_TOOLS)
        self.register_tools(GRAPH_TOOLS)
        self.register_prompts(BACKEND_PROMPTS)
        self.register_prompts(GRAPH_PROMPTS)
        
        # Register tool handler
        self.register_tool_handler("*", self._handle_backend_tool)
        
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
        
        # Set up MCP handlers
        self.setup_handlers()
    
    def _get_client(self) -> LogicBlokClient:
        # Get LogicBlok client with current API key
        api_key = self.get_api_key_for_request()
        if not api_key:
            raise ValueError("No API key available")
        return LogicBlokClient(api_key)
    
    async def _handle_backend_tool(self, name: str, arguments: dict) -> Any:
        # Handle all backend tool calls
        async with self._get_client() as client:
            # Route to appropriate client method
            if name == "list_projects":
                return await client.list_projects()
            elif name == "get_project":
                return await client.get_project(arguments["project_id"])
            elif name == "get_schema":
                return await client.get_schema(arguments["project_id"])
            elif name == "get_user_info":
                return await client.get_user_info()
            elif name == "get_job_status":
                return await client.get_job_status(arguments["job_id"])
            elif name == "get_project_info":
                return await client.get_project_info(arguments["project_id"])
            elif name == "get_version_history":
                return await client.get_version_history(arguments["project_id"])
            elif name == "get_template_schemas":
                return await client.get_template_schemas()
            elif name == "get_subscription_status":
                return await client.get_subscription_status()
            elif name == "get_project_usage":
                return await client.get_project_usage(arguments["project_id"])
            elif name == "get_schema_at_version":
                return await client.get_schema_at_version(
                    arguments["project_id"],
                    arguments["version"],
                )
            elif name == "create_project":
                return await client.create_project(
                    name=arguments["name"],
                    schema=arguments["schema"],
                    description=arguments.get("description"),
                )
            elif name == "update_schema":
                return await client.update_schema(
                    arguments["project_id"],
                    arguments["schema"],
                )
            elif name == "deploy_staging":
                return await client.deploy_staging(arguments["project_id"])
            elif name == "deploy_production":
                return await client.deploy_production(arguments["project_id"])
            elif name == "delete_project":
                return await client.delete_project(arguments["project_id"])
            elif name == "rollback_project":
                return await client.rollback_project(
                    project_id=arguments["project_id"],
                    version=arguments["version"],
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "rename_project":
                return await client.rename_project(
                    arguments["project_id"],
                    arguments["name"],
                )
            # ================================================================
            # Graph tool routing
            # ================================================================
            elif name == "get_graph_schema":
                return await client.get_graph_schema(arguments["project_id"])
            elif name == "get_graph_template_schemas":
                return await client.get_graph_template_schemas()
            elif name == "get_graph_version_history":
                return await client.get_graph_version_history(arguments["project_id"])
            elif name == "get_graph_schema_at_version":
                return await client.get_graph_schema_at_version(
                    arguments["project_id"],
                    arguments["version"],
                )
            elif name == "get_graph_project_info":
                return await client.get_graph_project_info(arguments["project_id"])
            elif name == "create_graph_project":
                return await client.create_graph_project(
                    name=arguments["name"],
                    schema=arguments["schema"],
                    description=arguments.get("description"),
                )
            elif name == "update_graph_schema":
                return await client.update_graph_schema(
                    arguments["project_id"],
                    arguments["schema"],
                )
            elif name == "deploy_graph_staging":
                return await client.deploy_graph_staging(arguments["project_id"])
            elif name == "deploy_graph_production":
                return await client.deploy_graph_production(arguments["project_id"])
            elif name == "delete_graph_project":
                return await client.delete_graph_project(arguments["project_id"])
            elif name == "rollback_graph_project":
                return await client.rollback_graph_project(
                    project_id=arguments["project_id"],
                    version=arguments["version"],
                    environment=arguments.get("environment", "staging"),
                )
            else:
                raise ValueError(f"Unknown backend tool: {name}")
    
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

AVAILABLE TYPES: string, text, integer, decimal, boolean, uuid, date, datetime, json

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

STRUCTURE:
{{
  "nodes": {{
    "EntityName": {{
      "description": "What this entity represents",
      "flat_labels": ["AdditionalLabel"],
      "schema": {{
        "required_fields": {{"field_name": "type"}},
        "optional_fields": {{"field_name": "type"}}
      }}
    }}
  }},
  "relationships": {{
    "RELATIONSHIP_TYPE": {{
      "from": "EntityName",
      "to": "OtherEntity",
      "cardinality": "MANY_TO_MANY",
      "data_schema": {{
        "optional_fields": {{"field_name": "type"}}
      }}
    }}
  }}
}}

FIELD TYPES: string, integer, float, boolean, date, json

CARDINALITY: ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY

RULES:
1. "nodes" key is REQUIRED — must contain at least one entity
2. Each entity needs "description" and "schema" with required/optional fields
3. Relationship "from"/"to" must reference defined node names
4. Relationship types: UPPER_SNAKE_CASE (e.g., FOLLOWS, CREATED_BY)
5. Entity names: PascalCase (e.g., Person, Product)
6. Nest entities inside parents to create type hierarchies
7. Automatic fields (id, created_at, updated_at) are NOT needed

HIERARCHICAL EXAMPLE:
{{
  "nodes": {{
    "Vehicle": {{
      "description": "A vehicle",
      "flat_labels": ["Transport"],
      "schema": {{
        "required_fields": {{"make": "string", "model": "string"}},
        "optional_fields": {{"year": "integer"}}
      }},
      "Car": {{
        "description": "A car (inherits Vehicle labels)",
        "flat_labels": ["Automobile"],
        "schema": {{
          "required_fields": {{"doors": "integer"}},
          "optional_fields": {{"electric": "boolean"}}
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
