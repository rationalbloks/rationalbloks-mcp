# RationalBloks MCP Tool Definitions
# Copyright © 2026 RationalBloks. All Rights Reserved.
#
# These define the tools available to AI agents via MCP protocol
# Must match the TOOL_REGISTRY in logicblok/mcp_gateway.py

TOOLS = [
    # =========================================================================
    # READ TOOLS (11 total)
    # =========================================================================
    {
        "name": "list_projects",
        "description": "List all your RationalBloks projects with their status and URLs",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_project",
        "description": "Get detailed information about a specific project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "get_schema",
        "description": "Get the JSON schema definition of a project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "get_user_info",
        "description": "Get information about the authenticated user",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_job_status",
        "description": "Check the status of a deployment job",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID returned from deployment operations"
                }
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "get_project_info",
        "description": "Get detailed project info including deployment status and resource usage",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "get_version_history",
        "description": "Get the deployment and version history (git commits) for a project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "get_template_schemas",
        "description": "Get available template schemas for creating new projects",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_subscription_status",
        "description": "Get your subscription tier, limits, and usage",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_project_usage",
        "description": "Get resource usage metrics (CPU, memory) for a project",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "get_schema_at_version",
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
            "required": ["project_id", "version"]
        }
    },
    
    # =========================================================================
    # WRITE TOOLS (7 total)
    # =========================================================================
    {
        "name": "create_project",
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
            "required": ["name", "schema"]
        }
    },
    {
        "name": "update_schema",
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
            "required": ["project_id", "schema"]
        }
    },
    {
        "name": "deploy_staging",
        "description": "Deploy a project to the staging environment",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "deploy_production",
        "description": "Promote staging to production (requires paid plan)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "delete_project",
        "description": "Delete a project (removes GitHub repo, K8s deployments, and database)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Project ID (UUID)"
                }
            },
            "required": ["project_id"]
        }
    },
    {
        "name": "rollback_project",
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
            "required": ["project_id", "version"]
        }
    },
    {
        "name": "rename_project",
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
            "required": ["project_id", "name"]
        }
    },
]
