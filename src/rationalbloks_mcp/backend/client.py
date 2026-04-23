# ============================================================================
# RATIONALBLOKS MCP - LOGICBLOK CLIENT
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# HTTP client for LogicBlok MCP Gateway (logicblok.rationalbloks.com/api/mcp)
# Uses the /api/mcp/execute endpoint with tool name + arguments pattern.
# ============================================================================

import httpx
import os
import ssl
import certifi
import json
from typing import Any

# Public API
__all__ = ["LogicBlokClient"]


class LogicBlokClient:
    # HTTP client for LogicBlok MCP Gateway
    # All operations go through POST /api/mcp/execute with tool name and arguments

    # LOGICBLOK_URL env var (set via K8s ConfigMap) lets in-cluster traffic stay
    # in-cluster (http://logicblok-api.logicblok.svc.cluster.local:8000).
    # Falls back to the public ingress for local / STDIO / dev use.
    BASE_URL = os.environ.get("LOGICBLOK_URL", "https://logicblok.rationalbloks.com")
    
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

    # Public alias -- preferred call path for the MCP tool dispatcher.
    # The dispatcher does not need per-tool wrappers; it passes the MCP tool
    # name straight through to the LogicBlok gateway.
    async def execute(self, tool: str, arguments: dict | None = None) -> Any:
        return await self._execute(tool, arguments)
