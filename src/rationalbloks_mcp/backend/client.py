# ============================================================================
# RATIONALBLOKS MCP - LOGICBLOK CLIENT
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# HTTP client for LogicBlok API (logicblok.rationalbloks.com)
# Handles all API communication for backend tools.
# ============================================================================

import httpx
import json
from typing import Any

# Public API
__all__ = ["LogicBlokClient"]


class LogicBlokClient:
    # HTTP client for LogicBlok API
    # Provides: Authentication via Bearer token, all backend API operations, proper error handling
    
    BASE_URL = "https://logicblok.rationalbloks.com"
    
    def __init__(self, api_key: str) -> None:
        # Initialize client with API key (rb_sk_...)
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
    
    async def close(self) -> None:
        # Close the HTTP client
        await self._client.aclose()
    
    async def __aenter__(self) -> "LogicBlokClient":
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
    
    # ========================================================================
    # READ OPERATIONS
    # ========================================================================
    
    async def list_projects(self) -> list[dict]:
        # List all projects for the authenticated user
        response = await self._client.get("/mcp/projects")
        response.raise_for_status()
        return response.json()
    
    async def get_project(self, project_id: str) -> dict:
        # Get details of a specific project
        response = await self._client.get(f"/mcp/projects/{project_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_project_info(self, project_id: str) -> dict:
        # Get detailed project info including deployment status
        response = await self._client.get(f"/mcp/projects/{project_id}/info")
        response.raise_for_status()
        return response.json()
    
    async def get_schema(self, project_id: str) -> dict:
        # Get the current schema for a project
        response = await self._client.get(f"/mcp/projects/{project_id}/schema")
        response.raise_for_status()
        return response.json()
    
    async def get_schema_at_version(self, project_id: str, version: str) -> dict:
        # Get schema at a specific version/commit
        response = await self._client.get(
            f"/mcp/projects/{project_id}/schema/version/{version}"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_version_history(self, project_id: str) -> list[dict]:
        # Get deployment history for a project
        response = await self._client.get(f"/mcp/projects/{project_id}/versions")
        response.raise_for_status()
        return response.json()
    
    async def get_job_status(self, job_id: str) -> dict:
        # Check the status of a deployment job
        response = await self._client.get(f"/mcp/jobs/{job_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_project_usage(self, project_id: str) -> dict:
        # Get resource usage metrics for a project
        response = await self._client.get(f"/mcp/projects/{project_id}/usage")
        response.raise_for_status()
        return response.json()
    
    async def get_user_info(self) -> dict:
        # Get information about the authenticated user
        response = await self._client.get("/mcp/user")
        response.raise_for_status()
        return response.json()
    
    async def get_subscription_status(self) -> dict:
        # Get subscription tier, limits, and usage
        response = await self._client.get("/mcp/subscription")
        response.raise_for_status()
        return response.json()
    
    async def get_template_schemas(self) -> dict:
        # Get pre-built template schemas for common use cases
        response = await self._client.get("/mcp/templates")
        response.raise_for_status()
        return response.json()
    
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
        payload = {"name": name, "schema": schema}
        if description:
            payload["description"] = description
        
        response = await self._client.post("/mcp/projects", json=payload)
        response.raise_for_status()
        return response.json()
    
    async def update_schema(self, project_id: str, schema: dict) -> dict:
        # Update a project's schema (does NOT deploy)
        # Returns: Updated project details
        response = await self._client.put(
            f"/mcp/projects/{project_id}/schema",
            json={"schema": schema},
        )
        response.raise_for_status()
        return response.json()
    
    async def deploy_staging(self, project_id: str) -> dict:
        # Deploy a project to staging environment
        # Returns: Deployment job details
        response = await self._client.post(
            f"/mcp/projects/{project_id}/deploy/staging"
        )
        response.raise_for_status()
        return response.json()
    
    async def deploy_production(self, project_id: str) -> dict:
        # Promote staging to production (requires paid plan)
        # Returns: Deployment job details
        response = await self._client.post(
            f"/mcp/projects/{project_id}/deploy/production"
        )
        response.raise_for_status()
        return response.json()
    
    async def delete_project(self, project_id: str) -> dict:
        # Delete a project and all associated resources
        # Returns: Deletion confirmation
        response = await self._client.delete(f"/mcp/projects/{project_id}")
        response.raise_for_status()
        return response.json()
    
    async def rollback_project(
        self,
        project_id: str,
        version: str,
        environment: str = "staging",
    ) -> dict:
        # Rollback a project to a previous version
        # Returns: Rollback job details
        response = await self._client.post(
            f"/mcp/projects/{project_id}/rollback",
            json={"version": version, "environment": environment},
        )
        response.raise_for_status()
        return response.json()
    
    async def rename_project(self, project_id: str, name: str) -> dict:
        # Rename a project (display name only)
        # Returns: Updated project details
        response = await self._client.patch(
            f"/mcp/projects/{project_id}",
            json={"name": name},
        )
        response.raise_for_status()
        return response.json()
