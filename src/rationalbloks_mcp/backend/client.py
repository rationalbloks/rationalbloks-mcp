# ============================================================================
# RATIONALBLOKS MCP - LOGICBLOK CLIENT
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# HTTP client for LogicBlok MCP Gateway (logicblok.rationalbloks.com/api/mcp)
# Uses the /api/mcp/execute endpoint with tool name + arguments pattern.
# ============================================================================

import httpx
import ssl
import certifi
import json
from typing import Any

# Public API
__all__ = ["LogicBlokClient"]


class LogicBlokClient:
    # HTTP client for LogicBlok MCP Gateway
    # All operations go through POST /api/mcp/execute with tool name and arguments
    
    BASE_URL = "https://logicblok.rationalbloks.com"
    
    def __init__(self, api_key: str) -> None:
        # Initialize client with API key (rb_sk_...)
        self.api_key = api_key
        # Use certifi for SSL certs (fixes issues in isolated uvx environments)
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=60.0,  # Longer timeout for deployment operations
            verify=ssl_context,
        )
    
    async def close(self) -> None:
        # Close the HTTP client
        await self._client.aclose()
    
    async def __aenter__(self) -> "LogicBlokClient":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
    
    async def _execute(self, tool: str, arguments: dict | None = None) -> Any:
        # Execute an MCP tool via the gateway
        # All tools use POST /api/mcp/execute with {"tool": "...", "arguments": {...}}
        payload = {"tool": tool, "arguments": arguments or {}}
        response = await self._client.post("/api/mcp/execute", json=payload)
        response.raise_for_status()
        result = response.json()
        
        # Gateway returns {"success": bool, "result": ..., "error": ...}
        if not result.get("success", False):
            error = result.get("error", "Unknown error")
            raise Exception(f"MCP Gateway error: {error}")
        
        return result.get("result")
    
    # ========================================================================
    # READ OPERATIONS
    # ========================================================================
    
    async def list_projects(self) -> list[dict]:
        # List all projects for the authenticated user
        return await self._execute("list_projects")
    
    async def get_project(self, project_id: str) -> dict:
        # Get details of a specific project
        return await self._execute("get_project", {"project_id": project_id})
    
    async def get_project_info(self, project_id: str) -> dict:
        # Get detailed project info including deployment status
        return await self._execute("get_project_info", {"project_id": project_id})
    
    async def get_schema(self, project_id: str) -> dict:
        # Get the current schema for a project
        return await self._execute("get_schema", {"project_id": project_id})
    
    async def get_schema_at_version(self, project_id: str, version: str) -> dict:
        # Get schema at a specific version/commit
        return await self._execute("get_schema_at_version", {
            "project_id": project_id,
            "version": version
        })
    
    async def get_version_history(self, project_id: str) -> list[dict]:
        # Get deployment history for a project
        return await self._execute("get_version_history", {"project_id": project_id})
    
    async def get_job_status(self, job_id: str) -> dict:
        # Check the status of a deployment job
        return await self._execute("get_job_status", {"job_id": job_id})
    
    async def get_project_usage(self, project_id: str) -> dict:
        # Get resource usage metrics for a project
        return await self._execute("get_project_usage", {"project_id": project_id})
    
    async def get_user_info(self) -> dict:
        # Get information about the authenticated user
        return await self._execute("get_user_info")
    
    async def get_subscription_status(self) -> dict:
        # Get subscription tier, limits, and usage
        return await self._execute("get_subscription_status")
    
    async def get_template_schemas(self) -> dict:
        # Get pre-built template schemas for common use cases
        return await self._execute("get_template_schemas")
    
    # ========================================================================
    # WRITE OPERATIONS
    # ========================================================================
    
    async def create_project(
        self,
        name: str,
        schema: dict,
        description: str | None = None,
    ) -> dict:
        # Create a new project from a JSON schema
        # Returns: Project details with job_id for deployment tracking
        args = {"name": name, "schema": schema}
        if description:
            args["description"] = description
        return await self._execute("create_project", args)
    
    async def update_schema(self, project_id: str, schema: dict) -> dict:
        # Update a project's schema (does NOT deploy)
        # Returns: Updated project details
        return await self._execute("update_schema", {
            "project_id": project_id,
            "schema": schema
        })
    
    async def deploy_staging(self, project_id: str) -> dict:
        # Deploy a project to staging environment
        # Returns: Deployment job details
        return await self._execute("deploy_staging", {"project_id": project_id})
    
    async def deploy_production(self, project_id: str) -> dict:
        # Promote staging to production (requires paid plan)
        # Returns: Deployment job details
        return await self._execute("deploy_production", {"project_id": project_id})
    
    async def delete_project(self, project_id: str) -> dict:
        # Delete a project and all associated resources
        # Returns: Deletion confirmation
        return await self._execute("delete_project", {"project_id": project_id})
    
    async def rollback_project(
        self,
        project_id: str,
        version: str,
        environment: str = "staging",
    ) -> dict:
        # Rollback a project to a previous version
        # Returns: Rollback job details
        return await self._execute("rollback_project", {
            "project_id": project_id,
            "version": version,
            "environment": environment
        })
    
    async def rename_project(self, project_id: str, name: str) -> dict:
        # Rename a project (display name only)
        # Returns: Updated project details
        return await self._execute("rename_project", {
            "project_id": project_id,
            "name": name
        })
