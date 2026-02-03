# ============================================================================
# RATIONALBLOKS MCP - BACKEND TOOLS
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# 18 Backend tools for API/database operations:
# READ (10): list_projects, get_project, get_schema, get_user_info,
#            get_job_status, get_project_info, get_version_history,
#            get_template_schemas, get_subscription_status, get_project_usage,
#            get_schema_at_version
# WRITE (8): create_project, update_schema, deploy_staging, deploy_production,
#            delete_project, rollback_project, rename_project
# ============================================================================

import os
import sys
from typing import Any

from mcp.types import Prompt, PromptArgument, PromptMessage, GetPromptResult, TextContent

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
    # --- WRITE OPERATIONS ---
    {
        "name": "create_project",
        "title": "Create Project",
        "description": """Create a new RationalBloks project from a JSON schema. ⚠️ CRITICAL: Schema MUST be in FLAT format (table_name → field_name → properties). DO NOT nest fields under a 'fields' key or the deployment will fail. ✅ CORRECT FORMAT: {users: {email: {type: string, required: true, unique: true}, name: {type: string, required: true}}, posts: {title: {type: string, required: true}, content: {type: text}, user_id: {type: uuid, foreign_key: users.id}}} ❌ WRONG FORMAT (will fail): {users: {fields: {email: {type: string}}}} ← DO NOT ADD 'fields' KEY. FIELD TYPES: string (varchar), text (long text), integer (whole numbers), decimal (decimal numbers), boolean (true/false), uuid (use for primary/foreign keys), date (date only), timestamp (date and time), json (JSON data). FIELD PROPERTIES: type (REQUIRED), required (boolean), unique (boolean), default (any), foreign_key (string format table.field), enum (array of allowed values). BEST PRACTICES: (1) Every field MUST have a 'type' property, (2) Use get_template_schemas to see complete examples, (3) Foreign keys use format 'table_name.id', (4) Primary keys auto-generated (don't define 'id' field), (5) Timestamps auto-generated (created_at, updated_at). After creation, use get_job_status with the returned job_id to monitor deployment.""",
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
        "description": """Update a project's schema (saves to database, does NOT deploy). ⚠️ CRITICAL: Schema MUST be in FLAT format (same as create_project). Every field MUST have a 'type' property or deployment will fail. ✅ CORRECT FORMAT: {users: {email: {type: string, required: true}, name: {type: string}}} ❌ WRONG: DO NOT nest under 'fields' key! NOTE: This only saves the schema. You must call deploy_staging afterwards to apply changes. Use get_schema first to see the current schema structure, then modify it. Use get_template_schemas to see valid schema examples.""",
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
# BACKEND MCP SERVER
# ============================================================================

class BackendMCPServer(BaseMCPServer):
    """Backend MCP server with 18 API/database tools.
    
    Extends BaseMCPServer with backend-specific:
    - LogicBlok client integration
    - 18 backend tools
    - Backend prompts
    """
    
    INSTRUCTIONS = """RationalBloks MCP Server - Backend Mode

Build production REST APIs from JSON schemas in seconds.

CRITICAL: Schema MUST be in FLAT format:
✅ {users: {email: {type: string}}} 
❌ {users: {fields: {email: {type: string}}}}

Available: 18 backend tools for projects, schemas, deployments.
Use get_template_schemas first to see correct format."""
    
    def __init__(
        self,
        api_key: str | None = None,
        http_mode: bool = False,
    ) -> None:
        """Initialize backend MCP server."""
        super().__init__(
            name="rationalbloks-backend",
            version="1.0.0",
            instructions=self.INSTRUCTIONS,
            api_key=api_key,
            http_mode=http_mode,
        )
        
        # Register backend tools and prompts
        self.register_tools(BACKEND_TOOLS)
        self.register_prompts(BACKEND_PROMPTS)
        
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
        
        # Set up MCP handlers
        self.setup_handlers()
    
    def _get_client(self) -> LogicBlokClient:
        """Get LogicBlok client with current API key."""
        api_key = self.get_api_key_for_request()
        if not api_key:
            raise ValueError("No API key available")
        return LogicBlokClient(api_key)
    
    async def _handle_backend_tool(self, name: str, arguments: dict) -> Any:
        """Handle all backend tool calls."""
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
            else:
                raise ValueError(f"Unknown backend tool: {name}")
    
    def _handle_create_project_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        """Handle create-project-from-description prompt."""
        description = arguments.get("description", "") if arguments else ""
        
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"""Create a RationalBloks project schema for: {description}

CRITICAL FORMAT RULES:
1. Schema MUST be FLAT: table_name → field_name → properties
2. Every field MUST have a 'type' property
3. DO NOT nest under 'fields' key

Example correct format:
{{
  "users": {{
    "email": {{"type": "string", "required": true, "unique": true}},
    "name": {{"type": "string", "required": true}}
  }},
  "posts": {{
    "title": {{"type": "string", "required": true}},
    "user_id": {{"type": "uuid", "foreign_key": "users.id"}}
  }}
}}

Available types: string, text, integer, decimal, boolean, uuid, date, timestamp, json

Generate the schema now:""",
                    ),
                )
            ]
        )
    
    def _handle_fix_schema_prompt(
        self,
        name: str,
        arguments: dict[str, str] | None,
    ) -> GetPromptResult:
        """Handle fix-schema-errors prompt."""
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

COMMON ISSUES:
1. Nested 'fields' key - REMOVE IT
2. Missing 'type' property - ADD IT
3. Wrong format - Use FLAT structure

Provide the corrected schema:""",
                    ),
                )
            ]
        )


def create_backend_server(
    api_key: str | None = None,
    http_mode: bool = False,
) -> BackendMCPServer:
    """Factory function to create a backend MCP server.
    
    Args:
        api_key: API key (required for STDIO mode)
        http_mode: If True, API key extracted per-request
    
    Returns:
        Configured BackendMCPServer instance
    """
    return BackendMCPServer(api_key=api_key, http_mode=http_mode)
