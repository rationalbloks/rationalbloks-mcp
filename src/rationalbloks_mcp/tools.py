# ============================================================================
# RATIONALBLOKS MCP TOOL DEFINITIONS
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# MCP Tool Registry - Follows MCP Specification 2025-06-18
# Each tool has: name, title, description, inputSchema, annotations
#
# Annotations (MCP Best Practice):
#   - readOnlyHint: True if tool does not modify state
#   - destructiveHint: True if tool performs destructive updates
#   - idempotentHint: True if repeated calls have no additional effect
#   - openWorldHint: True if tool interacts with external systems
#
# Categories:
#   - Read Operations (11): Query projects, schemas, status
#   - Write Operations (7): Create, update, deploy, delete
# ============================================================================

# Public API
__all__ = ["TOOLS"]

TOOLS = [
    # =========================================================================
    # READ TOOLS (11 total) - All readOnlyHint=True
    # =========================================================================
    {
        "name": "list_projects",
        "title": "List Projects",
        "description": "List all your RationalBloks projects with their status and URLs",
        "inputSchema": {
            "type": "object",
            "description": "No parameters required - returns all projects for authenticated user",
            "properties": {},
            "required": [],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "get_project",
        "title": "Get Project Details",
        "description": "Get detailed information about a specific project",
        "inputSchema": {
            "type": "object",
            "description": "Specify the project to retrieve",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "get_schema",
        "title": "Get Project Schema",
        "description": (
            "Get the JSON schema definition of a project in FLAT format. "
            "Returns the schema structure where each table name maps directly to field definitions. "
            "This is the same format required for create_project and update_schema. "
            "USE CASES: Review current schema before making updates, copy schema as template for new projects, verify schema structure after deployment, learn the correct schema format by example. "
            "The returned schema will be in FLAT format: {table_name: {field_name: {type, properties}}}"
        ),
        "inputSchema": {
            "type": "object",
            "description": "Specify the project whose schema to retrieve",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "get_user_info",
        "title": "Get User Information",
        "description": "Get information about the authenticated user",
        "inputSchema": {
            "type": "object",
            "description": "No parameters required - returns info for authenticated user",
            "properties": {},
            "required": [],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "get_job_status",
        "title": "Get Job Status",
        "description": (
            "Check the status of a deployment job. "
            "STATUS VALUES: pending (job queued), running (deployment in progress), completed (success), failed (deployment failed). "
            "TIMELINE: Typical deployment takes 2-5 minutes. If status is 'running' for >10 minutes, check get_project_info for detailed pod status. "
            "If status is 'failed', use get_project_info to see deployment errors and check schema format (must be FLAT, no 'fields' nesting)."
        ),
        "inputSchema": {
            "type": "object",
            "description": "Specify the job to check",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID returned from deployment operations"
                }
            },
            "required": ["job_id"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "get_project_info",
        "title": "Get Project Info",
        "description": (
            "Get detailed project info including deployment status and resource usage. "
            "DEPLOYMENT STATUS: Running (healthy), Pending (starting), CrashLoopBackOff (init container failed - usually schema format error), ImagePullBackOff (image build failed). "
            "TROUBLESHOOTING: If status is CrashLoopBackOff, the schema is likely in wrong format (nested 'fields' key or missing 'type' properties). Use get_schema to review current schema. "
            "If replicas show 0/2, the init container (migration runner) is failing. This is almost always a schema format issue."
        ),
        "inputSchema": {
            "type": "object",
            "description": "Specify the project to get info for",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "get_version_history",
        "title": "Get Version History",
        "description": (
            "Get the deployment and version history (git commits) for a project. "
            "Shows all schema changes with commit SHA, timestamp, and message. "
            "USE CASES: Review what changed between deployments, find the last working version before issues started, get commit SHA for rollback_project."
        ),
        "inputSchema": {
            "type": "object",
            "description": "Specify the project to get history for",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "get_template_schemas",
        "title": "Get Template Schemas",
        "description": (
            "Get pre-built template schemas for common use cases. "
            "⭐ USE THIS FIRST when creating a new project! "
            "Templates show the CORRECT schema format with: proper FLAT structure (no 'fields' nesting), every field has a 'type' property, foreign key relationships configured correctly, best practices for field naming and types. "
            "Available templates: E-commerce (products, orders, customers), Team collaboration (projects, tasks, users), General purpose templates. "
            "You can use these templates directly with create_project or modify them for your needs. "
            "TIP: Study these templates to understand the correct schema format before creating custom schemas."
        ),
        "inputSchema": {
            "type": "object",
            "description": "No parameters required - returns all available templates",
            "properties": {},
            "required": [],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "get_subscription_status",
        "title": "Get Subscription Status",
        "description": "Get your subscription tier, limits, and usage",
        "inputSchema": {
            "type": "object",
            "description": "No parameters required - returns subscription for authenticated user",
            "properties": {},
            "required": [],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "get_project_usage",
        "title": "Get Project Usage",
        "description": "Get resource usage metrics (CPU, memory) for a project",
        "inputSchema": {
            "type": "object",
            "description": "Specify the project to get usage metrics for",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "get_schema_at_version",
        "title": "Get Schema at Version",
        "description": "Get the schema as it was at a specific version/commit",
        "inputSchema": {
            "type": "object",
            "description": "Specify the project and version to retrieve schema for",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                },
                "version": {
                    "type": "string",
                    "description": "Commit SHA of the version"
                }
            },
            "required": ["project_id", "version"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },

    # =========================================================================
    # WRITE TOOLS (7 total) - Annotations vary by operation type
    # =========================================================================
    {
        "name": "create_project",
        "title": "Create Project",
        "description": (
            "Create a new RationalBloks project from a JSON schema. "
            "⚠️ CRITICAL: Schema MUST be in FLAT format (table_name → field_name → properties). DO NOT nest fields under a 'fields' key or the deployment will fail. "
            "✅ CORRECT FORMAT: {users: {email: {type: string, required: true, unique: true}, name: {type: string, required: true}}, posts: {title: {type: string, required: true}, content: {type: text}, user_id: {type: uuid, foreign_key: users.id}}} "
            "❌ WRONG FORMAT (will fail): {users: {fields: {email: {type: string}}}} ← DO NOT ADD 'fields' KEY. "
            "FIELD TYPES: string (varchar), text (long text), integer (whole numbers), decimal (decimal numbers), boolean (true/false), uuid (use for primary/foreign keys), date (date only), timestamp (date and time), json (JSON data). "
            "FIELD PROPERTIES: type (REQUIRED), required (boolean), unique (boolean), default (any), foreign_key (string format table.field), enum (array of allowed values). "
            "BEST PRACTICES: (1) Every field MUST have a 'type' property, (2) Use get_template_schemas to see complete examples, (3) Foreign keys use format 'table_name.id', (4) Primary keys auto-generated (don't define 'id' field), (5) Timestamps auto-generated (created_at, updated_at). "
            "After creation, use get_job_status with the returned job_id to monitor deployment."
        ),
        "inputSchema": {
            "type": "object",
            "description": "Project name, schema definition, and optional description",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Project name"
                },
                "schema": {
                    "type": "object",
                    "description": "JSON schema in FLAT format (table_name → field_name → properties). Every field MUST have a 'type' property. Use get_template_schemas to see valid examples."
                },
                "description": {
                    "type": "string",
                    "description": "Optional project description"
                }
            },
            "required": ["name", "schema"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True
        }
    },
    {
        "name": "update_schema",
        "title": "Update Schema",
        "description": (
            "Update a project's schema (saves to database, does NOT deploy). "
            "⚠️ CRITICAL: Schema MUST be in FLAT format (same as create_project). Every field MUST have a 'type' property or deployment will fail. "
            "✅ CORRECT FORMAT: {users: {email: {type: string, required: true}, name: {type: string}}} "
            "❌ WRONG: DO NOT nest under 'fields' key! "
            "NOTE: This only saves the schema. You must call deploy_staging afterwards to apply changes. "
            "Use get_schema first to see the current schema structure, then modify it. Use get_template_schemas to see valid schema examples."
        ),
        "inputSchema": {
            "type": "object",
            "description": "Project to update and new schema definition",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                },
                "schema": {
                    "type": "object",
                    "description": "New JSON schema in FLAT format (table_name → field_name → properties). Every field MUST have a 'type' property."
                }
            },
            "required": ["project_id", "schema"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
    {
        "name": "deploy_staging",
        "title": "Deploy to Staging",
        "description": (
            "Deploy a project to the staging environment. "
            "This triggers: (1) Schema validation, (2) Docker image build, (3) GitHub commit, (4) Kubernetes deployment, (5) Database migrations. "
            "The operation is ASYNCHRONOUS - it returns immediately with a job_id. Use get_job_status with the job_id to monitor progress. "
            "Deployment typically takes 2-5 minutes depending on schema complexity. "
            "If deployment fails, check: (1) Schema format is FLAT (no 'fields' nesting), (2) Every field has a 'type' property, (3) Foreign keys reference existing tables, (4) No PostgreSQL reserved words in table/field names. "
            "Use get_project_info to see if the deployment succeeded."
        ),
        "inputSchema": {
            "type": "object",
            "description": "Specify the project to deploy to staging",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    },
    {
        "name": "deploy_production",
        "title": "Deploy to Production",
        "description": "Promote staging to production (requires paid plan)",
        "inputSchema": {
            "type": "object",
            "description": "Specify the project to deploy to production",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True
        }
    },
    {
        "name": "delete_project",
        "title": "Delete Project",
        "description": "Delete a project (removes GitHub repo, K8s deployments, and database)",
        "inputSchema": {
            "type": "object",
            "description": "Specify the project to permanently delete",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True
        }
    },
    {
        "name": "rollback_project",
        "title": "Rollback Project",
        "description": (
            "Rollback a project to a previous version. "
            "⚠️ WARNING: This reverts schema AND code to the specified commit. Database data is NOT rolled back. "
            "Use get_version_history to find the commit SHA of the version you want to rollback to. "
            "After rollback, use get_job_status to monitor the redeployment. Rollback is useful when a schema change breaks deployment."
        ),
        "inputSchema": {
            "type": "object",
            "description": "Project, version, and environment for rollback",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                },
                "version": {
                    "type": "string",
                    "description": "Commit SHA or version to rollback to"
                },
                "environment": {
                    "type": "string",
                    "description": "Environment: staging or production (default: staging)"
                }
            },
            "required": ["project_id", "version"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": True
        }
    },
    {
        "name": "rename_project",
        "title": "Rename Project",
        "description": "Rename a project (changes display name, not project_code)",
        "inputSchema": {
            "type": "object",
            "description": "Project to rename and new display name",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                },
                "name": {
                    "type": "string",
                    "description": "New display name for the project"
                }
            },
            "required": ["project_id", "name"],
            "additionalProperties": False
        },
        "annotations": {
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False
        }
    },
]
