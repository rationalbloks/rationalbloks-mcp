# RationalBloks HTTP Client
# Copyright © 2026 RationalBloks. All Rights Reserved.
# Handles communication with the MCP Gateway

import httpx
from typing import Dict, Any, Optional

GATEWAY_URL = "https://logicblok.rationalbloks.com"


# ============================================================================
# HTTP CLIENT
# ============================================================================
# Handles authentication, request/response formatting, and error handling
# for all MCP tool executions.

class RationalBloksClient:
    
    def __init__(self, api_key: str, base_url: str = GATEWAY_URL):
        if not api_key:
            raise ValueError("API key is required")
            
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "rationalbloks-mcp/0.1.0"
            },
            timeout=60.0
        )
    
    def execute(self, tool: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Execute an MCP tool via the gateway
        # Args: tool (name), arguments (optional dict)
        # Returns: Dict with keys: success, result, error, job_id, poll_url
        payload = {
            "tool": tool,
            "arguments": arguments or {}
        }
        
        try:
            response = self._client.post("/api/mcp/execute", json=payload)
            
            if response.status_code == 401:
                return {"success": False, "error": "Invalid API key"}
            if response.status_code == 403:
                return {"success": False, "error": "Permission denied - check API key scopes"}
            if response.status_code == 429:
                return {"success": False, "error": "Rate limit exceeded - please wait"}
            if response.status_code == 503:
                return {"success": False, "error": "Service temporarily unavailable"}
            
            response.raise_for_status()
            return response.json()
            
        except httpx.ConnectError:
            return {"success": False, "error": "Cannot connect to RationalBloks - check your internet connection"}
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timed out - try again"}
        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"HTTP error {e.response.status_code}"}
    
    def list_tools(self) -> Dict[str, Any]:
        # Get available tools from the gateway
        response = self._client.get("/api/mcp/tools")
        response.raise_for_status()
        return response.json()
    
    def health(self) -> Dict[str, Any]:
        # Check gateway health
        response = self._client.get("/api/mcp/health")
        response.raise_for_status()
        return response.json()
    
    def close(self):
        # Close the HTTP client
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
