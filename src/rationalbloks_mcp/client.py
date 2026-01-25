# RationalBloks HTTP Client
# Copyright © 2026 RationalBloks. All Rights Reserved.
# Handles communication with the MCP Gateway
#
# AUTHENTICATION: OAuth2 Bearer Token (Authorization: Bearer rb_sk_...)
# TRANSPORT: HTTP/HTTPS with automatic retries and exponential backoff
# ERROR HANDLING: Production-grade error messages for all failure modes

import httpx
import time
from typing import Dict, Any, Optional

GATEWAY_URL = "https://logicblok.rationalbloks.com"
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds


# ============================================================================
# HTTP CLIENT
# ============================================================================
# Handles authentication, request/response formatting, error handling,
# and automatic retries for all MCP tool executions.

class RationalBloksClient:
    
    def __init__(self, api_key: str, base_url: str = GATEWAY_URL):
        """
        Initialize RationalBloks HTTP client.
        
        Args:
            api_key: RationalBloks API key (format: rb_sk_...)
            base_url: Gateway URL (default: https://logicblok.rationalbloks.com)
        
        Raises:
            ValueError: If API key is missing or invalid format
        """
        if not api_key:
            raise ValueError("API key is required")
        if not api_key.startswith("rb_sk_"):
            raise ValueError("Invalid API key format - must start with 'rb_sk_'")
            
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",  # OAuth2 Bearer Token
                "Content-Type": "application/json",
                "User-Agent": "rationalbloks-mcp/0.1.4"
            },
            timeout=60.0,
            follow_redirects=True
        )
    
    def execute(self, tool: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute an MCP tool via the gateway with automatic retries.
        
        Args:
            tool: Tool name (e.g., 'create_project', 'deploy_staging')
            arguments: Tool arguments (optional)
        
        Returns:
            Dict with keys:
                - success (bool): Whether the operation succeeded
                - result (Any): Tool result data (if success=True)
                - error (str): Error message (if success=False)
                - job_id (str): Async job ID (for long-running operations)
                - poll_url (str): URL to check job status
        
        Note: Automatically retries on network errors with exponential backoff.
        """
        payload = {
            "tool": tool,
            "arguments": arguments or {}
        }
        
        # Retry logic for transient failures
        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.post("/api/mcp/execute", json=payload)
                
                # Handle specific error codes
                if response.status_code == 401:
                    return {
                        "success": False, 
                        "error": "Invalid API key. Get your key from https://rationalbloks.com/settings"
                    }
                if response.status_code == 403:
                    return {
                        "success": False, 
                        "error": "Permission denied. Your API key doesn't have the required scope for this operation."
                    }
                if response.status_code == 429:
                    return {
                        "success": False, 
                        "error": "Rate limit exceeded. Please wait before making more requests."
                    }
                if response.status_code == 400:
                    # Bad request - parse error details
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("detail", "Invalid request")
                    except:
                        error_msg = response.text or "Invalid request"
                    return {"success": False, "error": error_msg}
                
                if response.status_code == 503:
                    # Service unavailable - retry
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (2 ** attempt))
                        continue
                    return {
                        "success": False, 
                        "error": "Service temporarily unavailable. Please try again later."
                    }
                
                response.raise_for_status()
                return response.json()
                
            except httpx.ConnectError:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))
                    continue
                return {
                    "success": False, 
                    "error": "Cannot connect to RationalBloks. Check your internet connection."
                }
            except httpx.TimeoutException:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))
                    continue
                return {
                    "success": False, 
                    "error": "Request timed out. The operation may still be in progress."
                }
            except httpx.HTTPStatusError as e:
                return {
                    "success": False, 
                    "error": f"HTTP {e.response.status_code}: {e.response.text or 'Unknown error'}"
                }
            except Exception as e:
                return {
                    "success": False, 
                    "error": f"Unexpected error: {type(e).__name__}: {str(e)}"
                }
        
        return {
            "success": False, 
            "error": f"Max retries ({MAX_RETRIES}) exceeded. Please try again later."
        }
    
    def list_tools(self) -> Dict[str, Any]:
        """
        Get available MCP tools from the gateway.
        
        Returns:
            Dict with tool list, authentication info, and rate limits
        """
        try:
            response = self._client.get("/api/mcp/tools")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fetch tools: {str(e)}"
            }
    
    def health(self) -> Dict[str, Any]:
        """
        Check MCP gateway health status.
        
        Returns:
            Dict with status, version, and timestamp
        """
        try:
            response = self._client.get("/api/mcp/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e)
            }
    
    def close(self):
        """Close the HTTP client and release resources."""
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def __del__(self):
        """Ensure client is closed on garbage collection."""
        try:
            self.close()
        except:
            pass
