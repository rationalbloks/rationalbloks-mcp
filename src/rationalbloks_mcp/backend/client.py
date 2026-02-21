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
    
    # ========================================================================
    # GRAPH READ OPERATIONS
    # ========================================================================
    
    async def get_graph_schema(self, project_id: str) -> dict:
        # Get the graph schema (nodes and relationships) for a project
        return await self._execute("get_graph_schema", {"project_id": project_id})
    
    async def get_graph_template_schemas(self) -> dict:
        # Get pre-built graph template schemas for common use cases
        return await self._execute("get_graph_template_schemas")
    
    async def get_graph_version_history(self, project_id: str) -> dict:
        # Get deployment/version history for a graph project
        return await self._execute("get_graph_version_history", {"project_id": project_id})
    
    async def get_graph_schema_at_version(self, project_id: str, version: str) -> dict:
        # Get graph schema at a specific version/commit
        return await self._execute("get_graph_schema_at_version", {
            "project_id": project_id,
            "version": version
        })
    
    async def get_graph_project_info(self, project_id: str) -> dict:
        # Get detailed graph project info including K8s and Neo4j status
        return await self._execute("get_graph_project_info", {"project_id": project_id})
    
    # ========================================================================
    # GRAPH WRITE OPERATIONS
    # ========================================================================
    
    async def create_graph_project(
        self,
        name: str,
        schema: dict,
        description: str | None = None,
    ) -> dict:
        # Create a new Neo4j graph project from a hierarchical schema
        # Returns: Project details with job_id for deployment tracking
        args = {"name": name, "schema": schema}
        if description:
            args["description"] = description
        return await self._execute("create_graph_project", args)
    
    async def update_graph_schema(self, project_id: str, schema: dict) -> dict:
        # Update a graph project's schema (does NOT deploy)
        # Returns: Updated project details
        return await self._execute("update_graph_schema", {
            "project_id": project_id,
            "schema": schema
        })
    
    async def deploy_graph_staging(self, project_id: str) -> dict:
        # Deploy a graph project to staging environment
        # Returns: Deployment job details
        return await self._execute("deploy_graph_staging", {"project_id": project_id})
    
    async def deploy_graph_production(self, project_id: str) -> dict:
        # Promote graph staging to production (requires paid plan)
        # Returns: Deployment job details
        return await self._execute("deploy_graph_production", {"project_id": project_id})
    
    async def delete_graph_project(self, project_id: str) -> dict:
        # Delete a graph project and all associated resources
        # Returns: Deletion confirmation
        return await self._execute("delete_graph_project", {"project_id": project_id})
    
    async def rollback_graph_project(
        self,
        project_id: str,
        version: str,
        environment: str = "staging",
    ) -> dict:
        # Rollback a graph project to a previous version
        # Returns: Rollback result
        return await self._execute("rollback_graph_project", {
            "project_id": project_id,
            "version": version,
            "environment": environment
        })

    # ========================================================================
    # GRAPH DATA OPERATIONS
    # ========================================================================

    async def create_graph_node(
        self,
        project_id: str,
        entity_type: str,
        entity_id: str,
        data: dict,
        environment: str = "staging",
    ) -> dict:
        # Create a single node in a deployed graph project
        return await self._execute("create_graph_node", {
            "project_id": project_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "data": data,
            "environment": environment,
        })

    async def get_graph_node(
        self,
        project_id: str,
        entity_type: str,
        entity_id: str,
        environment: str = "staging",
    ) -> dict:
        # Get a specific node by entity_id
        return await self._execute("get_graph_node", {
            "project_id": project_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "environment": environment,
        })

    async def list_graph_nodes(
        self,
        project_id: str,
        entity_type: str,
        limit: int = 100,
        offset: int = 0,
        environment: str = "staging",
    ) -> dict:
        # List nodes of a specific entity type
        return await self._execute("list_graph_nodes", {
            "project_id": project_id,
            "entity_type": entity_type,
            "limit": limit,
            "offset": offset,
            "environment": environment,
        })

    async def update_graph_node(
        self,
        project_id: str,
        entity_type: str,
        entity_id: str,
        data: dict,
        environment: str = "staging",
    ) -> dict:
        # Update properties of an existing node
        return await self._execute("update_graph_node", {
            "project_id": project_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "data": data,
            "environment": environment,
        })

    async def delete_graph_node(
        self,
        project_id: str,
        entity_type: str,
        entity_id: str,
        environment: str = "staging",
    ) -> dict:
        # Delete a node and all its relationships
        return await self._execute("delete_graph_node", {
            "project_id": project_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "environment": environment,
        })

    async def create_graph_relationship(
        self,
        project_id: str,
        rel_type: str,
        from_id: str,
        to_id: str,
        data: dict | None = None,
        environment: str = "staging",
    ) -> dict:
        # Create a relationship between two nodes
        args = {
            "project_id": project_id,
            "rel_type": rel_type,
            "from_id": from_id,
            "to_id": to_id,
            "environment": environment,
        }
        if data:
            args["data"] = data
        return await self._execute("create_graph_relationship", args)

    async def get_node_relationships(
        self,
        project_id: str,
        entity_type: str,
        entity_id: str,
        direction: str = "both",
        rel_type_filter: str | None = None,
        environment: str = "staging",
    ) -> dict:
        # Get all relationships connected to a node
        args = {
            "project_id": project_id,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "direction": direction,
            "environment": environment,
        }
        if rel_type_filter:
            args["rel_type_filter"] = rel_type_filter
        return await self._execute("get_node_relationships", args)

    async def delete_graph_relationship(
        self,
        project_id: str,
        rel_type: str,
        rel_id: int,
        environment: str = "staging",
    ) -> dict:
        # Delete a specific relationship by ID
        return await self._execute("delete_graph_relationship", {
            "project_id": project_id,
            "rel_type": rel_type,
            "rel_id": rel_id,
            "environment": environment,
        })

    async def bulk_create_graph_nodes(
        self,
        project_id: str,
        entity_type: str,
        nodes: list,
        environment: str = "staging",
    ) -> dict:
        # Bulk create up to 500 nodes at once
        return await self._execute("bulk_create_graph_nodes", {
            "project_id": project_id,
            "entity_type": entity_type,
            "nodes": nodes,
            "environment": environment,
        })

    async def bulk_create_graph_relationships(
        self,
        project_id: str,
        rel_type: str,
        relationships: list,
        environment: str = "staging",
    ) -> dict:
        # Bulk create up to 500 relationships at once
        return await self._execute("bulk_create_graph_relationships", {
            "project_id": project_id,
            "rel_type": rel_type,
            "relationships": relationships,
            "environment": environment,
        })

    async def search_graph_nodes(
        self,
        project_id: str,
        filters: dict,
        entity_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
        environment: str = "staging",
    ) -> dict:
        # Search nodes by property values
        args = {
            "project_id": project_id,
            "filters": filters,
            "limit": limit,
            "offset": offset,
            "environment": environment,
        }
        if entity_type:
            args["entity_type"] = entity_type
        return await self._execute("search_graph_nodes", args)

    async def traverse_graph(
        self,
        project_id: str,
        start_entity_type: str,
        start_entity_id: str,
        max_depth: int = 3,
        relationship_types: list | None = None,
        direction: str = "both",
        limit: int = 100,
        environment: str = "staging",
    ) -> dict:
        # Traverse the graph from a starting node
        args = {
            "project_id": project_id,
            "start_entity_type": start_entity_type,
            "start_entity_id": start_entity_id,
            "max_depth": max_depth,
            "direction": direction,
            "limit": limit,
            "environment": environment,
        }
        if relationship_types:
            args["relationship_types"] = relationship_types
        return await self._execute("traverse_graph", args)

    async def get_graph_statistics(
        self,
        project_id: str,
        environment: str = "staging",
    ) -> dict:
        # Get graph database statistics (node/relationship counts)
        return await self._execute("get_graph_statistics", {
            "project_id": project_id,
            "environment": environment,
        })

    async def get_graph_data_schema(
        self,
        project_id: str,
        environment: str = "staging",
    ) -> dict:
        # Get the runtime schema (entity types and relationship types) from deployed API
        return await self._execute("get_graph_data_schema", {
            "project_id": project_id,
            "environment": environment,
        })
