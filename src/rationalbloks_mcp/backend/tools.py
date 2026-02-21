# ============================================================================
# RATIONALBLOKS MCP - BACKEND TOOLS
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# 48 Backend tools (18 relational + 11 graph schema + 15 graph data + 4 knowledge):
#
# RELATIONAL (18):
#   READ (11): list_projects, get_project, get_schema, get_user_info,
#              get_job_status, get_project_info, get_version_history,
#              get_template_schemas, get_subscription_status, get_project_usage,
#              get_schema_at_version
#   WRITE (7): create_project, update_schema, deploy_staging, deploy_production,
#              delete_project, rollback_project, rename_project
#
# GRAPH SCHEMA (11):
#   READ (5):  get_graph_schema, get_graph_template_schemas,
#              get_graph_version_history, get_graph_schema_at_version,
#              get_graph_project_info
#   WRITE (6): create_graph_project, update_graph_schema,
#              deploy_graph_staging, deploy_graph_production,
#              delete_graph_project, rollback_graph_project
#
# GRAPH DATA (15):
#   READ (8):  get_graph_node, list_graph_nodes, get_node_relationships,
#              search_graph_nodes, fulltext_search_graph, traverse_graph,
#              get_graph_statistics, get_graph_data_schema
#   WRITE (7): create_graph_node, update_graph_node, delete_graph_node,
#              create_graph_relationship, delete_graph_relationship,
#              bulk_create_graph_nodes, bulk_create_graph_relationships
#
# KNOWLEDGE (4):
#   READ (2):  get_processing_job, list_processing_jobs
#   WRITE (2): process_content, process_url
# ============================================================================

from typing import Any

from mcp.types import Prompt, PromptArgument, PromptMessage, GetPromptResult, TextContent

from .. import __version__
from ..core import BaseMCPServer
from .client import LogicBlokClient

# Public API
__all__ = [
    "BACKEND_TOOLS",
    "GRAPH_TOOLS",
    "GRAPH_DATA_TOOLS",
    "KNOWLEDGE_TOOLS",
    "BACKEND_PROMPTS",
    "GRAPH_PROMPTS",
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
        "description": """Get pre-built graph template schemas for common use cases. ⭐ USE THIS FIRST when creating a new graph project! Templates show the CORRECT graph schema format with: proper node definitions (description, flat_labels, schema with flat field definitions), relationship configurations (from, to, cardinality, data_schema), and hierarchical entity nesting. Available templates: Social Network (users, posts, follows), Knowledge Graph (topics, articles, authors), Product Catalog (products, categories, suppliers). You can use these templates directly with create_graph_project or modify them for your needs. TIP: Study these templates to understand the correct graph schema format before creating custom schemas.""",
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
        "name": {"type": "string", "required": true},
        "habitat": {"type": "string"}
      },
      "Dog": {
        "description": "A dog (inherits Animal labels)",
        "flat_labels": ["Pet"],
        "schema": {
          "breed": {"type": "string", "required": true},
          "trained": {"type": "boolean"}
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
2. Each entity needs "description" and "schema" with field definitions
3. Each field is {"type": "...", "required": true/false} — required defaults to false
4. Relationship "from"/"to" must reference defined node names
5. Relationship types should be UPPER_SNAKE_CASE
6. Entity names should be PascalCase
7. Automatic fields (id, created_at, updated_at) are NOT needed
8. Use get_graph_template_schemas FIRST to see valid examples

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
• Each entity needs "description" and "schema" with field definitions
• Each field is {"type": "...", "required": true/false} — required defaults to false
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
# GRAPH DATA TOOLS (15 tools for operating on graph data via deployed APIs)
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
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
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
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True}
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
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True}
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
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
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
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": True}
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
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
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
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
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
# KNOWLEDGE PROCESSING TOOLS (4 tools)
# ============================================================================
# Tools for automated AI content processing into Knowledge Graphs.
# These connect to the Graforest service for server-side AI extraction.
# ============================================================================

KNOWLEDGE_TOOLS = [
    {
        "name": "process_content",
        "title": "Process Content to Knowledge Graph",
        "description": "Submit text content for AI-powered extraction into a Knowledge Graph. The server chunks the content, sends it to the best AI model for entity/relationship extraction, and populates the graph automatically. Returns a job ID for tracking progress. Supports quality levels: fast (GPT-4o-mini), balanced (Claude Sonnet), thorough (Claude Opus).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Target graph project ID (UUID)"},
                "content": {"type": "string", "description": "Text content to process (max 500K characters)"},
                "environment": {"type": "string", "description": "staging or production (default: staging)"},
                "quality": {"type": "string", "enum": ["fast", "balanced", "thorough"], "description": "Extraction quality level (default: balanced)"},
                "source_name": {"type": "string", "description": "Source identifier (e.g., book title, article name)"},
            },
            "required": ["project_id", "content"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
    },
    {
        "name": "process_url",
        "title": "Process URL to Knowledge Graph",
        "description": "Scrape a URL, extract its content, and process it into a Knowledge Graph using AI. The server fetches the page, extracts clean text, chunks it, runs AI extraction, and populates the graph. Returns a job ID for tracking.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Target graph project ID (UUID)"},
                "url": {"type": "string", "description": "URL to scrape and process"},
                "environment": {"type": "string", "description": "staging or production (default: staging)"},
                "quality": {"type": "string", "enum": ["fast", "balanced", "thorough"], "description": "Extraction quality level (default: balanced)"},
            },
            "required": ["project_id", "url"]
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": True}
    },
    {
        "name": "get_processing_job",
        "title": "Get Processing Job Status",
        "description": "Check the status of an AI content processing job. Returns progress (chunks processed, entities created, relationships created), timing, AI model used, and token usage.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Processing job ID (UUID)"},
            },
            "required": ["job_id"]
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
    },
    {
        "name": "list_processing_jobs",
        "title": "List Processing Jobs",
        "description": "List all AI content processing jobs. Optionally filter by project. Shows status, progress, and results for each job.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Filter by project ID (optional)"},
                "limit": {"type": "integer", "description": "Max results (default: 50)"},
                "offset": {"type": "integer", "description": "Pagination offset (default: 0)"},
            },
            "required": []
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
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
    Prompt(
        name="process-content-to-knowledge-graph",
        title="Process Content to Knowledge Graph",
        description="Extract entities and relationships from text content and populate a knowledge graph using MCP tools. Provide the content and the project ID of an existing graph project.",
        arguments=[
            PromptArgument(
                name="content",
                description="The text content to extract knowledge from (article, book chapter, document, etc.)",
                required=True,
            ),
            PromptArgument(
                name="project_id",
                description="The project ID (UUID) of the target graph project that already has a deployed schema",
                required=True,
            ),
            PromptArgument(
                name="environment",
                description="Target environment: staging or production (default: staging)",
                required=False,
            ),
        ],
    ),
]


# ============================================================================
# BACKEND MCP SERVER
# ============================================================================

class BackendMCPServer(BaseMCPServer):
    # Backend MCP server with 48 tools (18 relational + 11 graph schema + 15 graph data + 4 knowledge)
    # Extends BaseMCPServer with: LogicBlok client integration, backend + graph tools, prompts
    
    INSTRUCTIONS = """RationalBloks MCP Server — Backend Mode

Build production REST APIs and Graph APIs from JSON schemas in seconds.

═══════════════════════════════════════════════════════════════════════════
TWO PROJECT TYPES:
═══════════════════════════════════════════════════════════════════════════

1. RELATIONAL (PostgreSQL) — Flat table schemas, SQL databases, CRUD APIs
   Tools: create_project, get_schema, deploy_staging, etc. (18 tools)

2. GRAPH (Neo4j) — Hierarchical node/relationship schemas, graph databases
   Schema tools: create_graph_project, get_graph_schema, deploy_graph_staging, etc. (11 tools)
   Data tools: create_graph_node, bulk_create_graph_nodes, search_graph_nodes, etc. (15 tools)

═══════════════════════════════════════════════════════════════════════════
GRAPH DATA OPERATIONS (Knowledge Graph Population):
═══════════════════════════════════════════════════════════════════════════

After deploying a graph project, use these tools to populate and query data:

1. get_graph_data_schema — See available entity types and relationship types
2. create_graph_node / bulk_create_graph_nodes — Add knowledge nodes
3. create_graph_relationship / bulk_create_graph_relationships — Connect knowledge
4. search_graph_nodes — Find nodes by specific properties
5. fulltext_search_graph — Search across ALL text fields at once
6. traverse_graph — Walk connections from any node
7. get_graph_statistics — Get counts and overview

KNOWLEDGE GRAPH WORKFLOW:
1. create_graph_project → Design schema for your knowledge domain
2. deploy_graph_staging → Infrastructure spins up
3. get_graph_data_schema → See entity types & relationships
4. bulk_create_graph_nodes → Populate entities from content
5. bulk_create_graph_relationships → Connect the knowledge
6. fulltext_search_graph → Search the knowledge (free-text)
7. search_graph_nodes → Filter by specific properties
8. traverse_graph → Explore connections

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
2. FLAT FIELD FORMAT (same as relational): {"field": {"type": "string", "required": true}}
3. Field types: string, integer, float, boolean, date, json
4. Cardinality: ONE_TO_ONE, ONE_TO_MANY, MANY_TO_ONE, MANY_TO_MANY
5. Entity names: PascalCase | Relationship types: UPPER_SNAKE_CASE
6. Nest entities inside parents to create type hierarchies
7. DON'T define: id, created_at, updated_at (automatic)
8. Use get_graph_template_schemas FIRST to see valid examples

Available: 48 tools (18 relational + 11 graph schema + 15 graph data + 4 knowledge).
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
        self.register_tools(GRAPH_DATA_TOOLS)
        self.register_tools(KNOWLEDGE_TOOLS)
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
        self.register_prompt_handler(
            "process-content-to-knowledge-graph",
            self._handle_process_content_prompt,
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
            # ============================================================
            # Graph data tool routing
            # ============================================================
            elif name == "create_graph_node":
                return await client.create_graph_node(
                    project_id=arguments["project_id"],
                    entity_type=arguments["entity_type"],
                    entity_id=arguments["entity_id"],
                    data=arguments["data"],
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "get_graph_node":
                return await client.get_graph_node(
                    project_id=arguments["project_id"],
                    entity_type=arguments["entity_type"],
                    entity_id=arguments["entity_id"],
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "list_graph_nodes":
                return await client.list_graph_nodes(
                    project_id=arguments["project_id"],
                    entity_type=arguments["entity_type"],
                    limit=arguments.get("limit", 100),
                    offset=arguments.get("offset", 0),
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "update_graph_node":
                return await client.update_graph_node(
                    project_id=arguments["project_id"],
                    entity_type=arguments["entity_type"],
                    entity_id=arguments["entity_id"],
                    data=arguments["data"],
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "delete_graph_node":
                return await client.delete_graph_node(
                    project_id=arguments["project_id"],
                    entity_type=arguments["entity_type"],
                    entity_id=arguments["entity_id"],
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "create_graph_relationship":
                return await client.create_graph_relationship(
                    project_id=arguments["project_id"],
                    rel_type=arguments["rel_type"],
                    from_id=arguments["from_id"],
                    to_id=arguments["to_id"],
                    data=arguments.get("data", {}),
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "get_node_relationships":
                return await client.get_node_relationships(
                    project_id=arguments["project_id"],
                    entity_type=arguments["entity_type"],
                    entity_id=arguments["entity_id"],
                    direction=arguments.get("direction", "both"),
                    rel_type_filter=arguments.get("rel_type_filter"),
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "delete_graph_relationship":
                return await client.delete_graph_relationship(
                    project_id=arguments["project_id"],
                    rel_type=arguments["rel_type"],
                    rel_id=arguments["rel_id"],
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "bulk_create_graph_nodes":
                return await client.bulk_create_graph_nodes(
                    project_id=arguments["project_id"],
                    entity_type=arguments["entity_type"],
                    nodes=arguments["nodes"],
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "bulk_create_graph_relationships":
                return await client.bulk_create_graph_relationships(
                    project_id=arguments["project_id"],
                    rel_type=arguments["rel_type"],
                    relationships=arguments["relationships"],
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "search_graph_nodes":
                return await client.search_graph_nodes(
                    project_id=arguments["project_id"],
                    filters=arguments["filters"],
                    entity_type=arguments.get("entity_type"),
                    limit=arguments.get("limit", 100),
                    offset=arguments.get("offset", 0),
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "fulltext_search_graph":
                return await client.fulltext_search_graph(
                    project_id=arguments["project_id"],
                    query=arguments["query"],
                    entity_type=arguments.get("entity_type"),
                    limit=arguments.get("limit", 50),
                    offset=arguments.get("offset", 0),
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "traverse_graph":
                return await client.traverse_graph(
                    project_id=arguments["project_id"],
                    start_entity_type=arguments["start_entity_type"],
                    start_entity_id=arguments["start_entity_id"],
                    max_depth=arguments.get("max_depth", 3),
                    relationship_types=arguments.get("relationship_types"),
                    direction=arguments.get("direction", "both"),
                    limit=arguments.get("limit", 100),
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "get_graph_statistics":
                return await client.get_graph_statistics(
                    project_id=arguments["project_id"],
                    environment=arguments.get("environment", "staging"),
                )
            elif name == "get_graph_data_schema":
                return await client.get_graph_data_schema(
                    project_id=arguments["project_id"],
                    environment=arguments.get("environment", "staging"),
                )
            # Knowledge processing tools
            elif name == "process_content":
                return await client.process_content(
                    project_id=arguments["project_id"],
                    content=arguments["content"],
                    environment=arguments.get("environment", "staging"),
                    quality=arguments.get("quality", "balanced"),
                    source_name=arguments.get("source_name"),
                )
            elif name == "process_url":
                return await client.process_url(
                    project_id=arguments["project_id"],
                    url=arguments["url"],
                    environment=arguments.get("environment", "staging"),
                    quality=arguments.get("quality", "balanced"),
                )
            elif name == "get_processing_job":
                return await client.get_processing_job(
                    job_id=arguments["job_id"],
                )
            elif name == "list_processing_jobs":
                return await client.list_processing_jobs(
                    project_id=arguments.get("project_id"),
                    limit=arguments.get("limit", 50),
                    offset=arguments.get("offset", 0),
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

    def _handle_process_content_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        # Handle process-content-to-knowledge-graph prompt
        content = arguments.get("content", "") if arguments else ""
        project_id = arguments.get("project_id", "") if arguments else ""
        environment = arguments.get("environment", "staging") if arguments else "staging"
        
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Extract knowledge from the following content and populate the knowledge graph.

═══════════════════════════════════════════════════════════════════════════
TARGET GRAPH PROJECT
═══════════════════════════════════════════════════════════════════════════
Project ID: {project_id}
Environment: {environment}

═══════════════════════════════════════════════════════════════════════════
WORKFLOW — FOLLOW THESE STEPS IN ORDER:
═══════════════════════════════════════════════════════════════════════════

STEP 1: DISCOVER THE SCHEMA
   Call get_graph_data_schema with project_id="{project_id}" and environment="{environment}"
   This tells you the available entity types (nodes) and relationship types.
   Study the schema carefully — you can ONLY create nodes and relationships
   that match the defined schema.

STEP 2: ANALYZE THE CONTENT
   Read the content below and identify:
   • Entities (people, concepts, places, organizations, events, etc.)
   • Relationships between entities (who relates to whom, how)
   • Properties of each entity (names, descriptions, dates, attributes)
   • Properties of relationships (dates, weights, descriptions)
   
   Map each discovered entity to the closest matching entity type in the schema.
   Map each discovered relationship to the closest matching relationship type.
   Skip any entities or relationships that don't fit the schema.

STEP 3: CREATE ENTITIES WITH BULK OPERATIONS
   Use bulk_create_graph_nodes to efficiently create entities in batches.
   For each entity type found in the content:
   • Gather all entities of that type
   • Create unique entity_id values (use slugified names: "albert-einstein", "theory-of-relativity")
   • Batch them in groups of up to 500
   • Call bulk_create_graph_nodes for each entity type

   ENTITY ID RULES:
   • Use lowercase-kebab-case: "quantum-mechanics", "isaac-newton"
   • Must be unique within an entity type
   • Should be human-readable and deterministic (same content → same IDs)
   • Avoid generic IDs like "entity-1" — use meaningful names

STEP 4: CREATE RELATIONSHIPS WITH BULK OPERATIONS
   Use bulk_create_graph_relationships to connect entities.
   For each relationship type found:
   • Gather all relationships of that type
   • Use the entity_id values from Step 3 as from_id and to_id
   • Include any relationship properties from the content
   • Batch them in groups of up to 500
   • Call bulk_create_graph_relationships for each type

STEP 5: VERIFY THE GRAPH
   Call get_graph_statistics to confirm the data was created.
   Report a summary: how many nodes and relationships were created,
   organized by type.

═══════════════════════════════════════════════════════════════════════════
KNOWLEDGE EXTRACTION GUIDELINES
═══════════════════════════════════════════════════════════════════════════

ENTITY EXTRACTION:
• Extract ALL meaningful entities — be comprehensive, not selective
• Prefer specific entities over vague ones ("Albert Einstein" > "a scientist")
• Include both major and supporting entities
• Preserve original names and terminology from the content
• Add descriptive properties: summaries, categories, dates, quotes

RELATIONSHIP EXTRACTION:
• Extract explicit relationships stated in the text
• Infer implicit relationships when strongly supported by context
• Include temporal relationships (before, after, during)
• Include causal relationships (caused, influenced, led to)
• Include hierarchical relationships (part of, type of, belongs to)
• Add relationship properties when available (date, strength, context)

QUALITY RULES:
• Never invent facts not present or strongly implied in the content
• When uncertain about a relationship, skip it rather than guess
• Deduplicate: same real-world entity → same entity_id
• Cross-reference: if "Einstein" and "Albert Einstein" refer to the same
  person, use the same entity_id

═══════════════════════════════════════════════════════════════════════════
CONTENT TO PROCESS
═══════════════════════════════════════════════════════════════════════════

{content}

═══════════════════════════════════════════════════════════════════════════

Begin by calling get_graph_data_schema, then extract and populate the knowledge graph:""",
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
