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
        "description": "Get the JSON schema definition of a project",
        "inputSchema": {
            "type": "object",
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
        "description": "Check the status of a deployment job",
        "inputSchema": {
            "type": "object",
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
        "description": "Get detailed project info including deployment status and resource usage",
        "inputSchema": {
            "type": "object",
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
        "description": "Get the deployment and version history (git commits) for a project",
        "inputSchema": {
            "type": "object",
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
        "description": "Get available template schemas for creating new projects",
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
        "description": "Create a new RationalBloks project from a JSON schema",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Project name"
                },
                "schema": {
                    "type": "object",
                    "description": "JSON schema defining your data model with tables and fields"
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
        "description": "Update a project's schema (saves to database, does NOT deploy)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                },
                "schema": {
                    "type": "object",
                    "description": "New JSON schema for the project"
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
        "description": "Deploy a project to the staging environment",
        "inputSchema": {
            "type": "object",
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
        "description": "Rollback a project to a previous version",
        "inputSchema": {
            "type": "object",
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
