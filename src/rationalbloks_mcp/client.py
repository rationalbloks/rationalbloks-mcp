# ============================================================================
# RATIONALBLOKS HTTP CLIENT
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Handles communication with MCP Gateway at logicblok.rationalbloks.com
#
# AUTHENTICATION: OAuth2 Bearer Token (Authorization: Bearer rb_sk_...)
# TRANSPORT: HTTPS with automatic retries and exponential backoff
# ERROR HANDLING: Fail-fast chain - if one step fails, entire operation fails
#
# CHAIN MANTRA ENFORCEMENT:
# - Single top-level try/except per function
# - One correct path through code (no branching error handling)
# - If any step fails, entire chain fails immediately
# - Clear error messages for all failure modes
# ============================================================================

import httpx
import time
from typing import Any

# Version - read dynamically to avoid circular import
try:
    from importlib.metadata import version as _get_version
    __version__ = _get_version("rationalbloks-mcp")
except Exception:
    __version__ = "0.1.8"

GATEWAY_URL = "https://logicblok.rationalbloks.com"
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # Base delay in seconds, exponentially increases


class RationalBloksClient:
    # HTTP client for MCP Gateway communication
    # Validates API key format on initialization
    # Provides execute(), list_tools(), and health() methods
    
    def __init__(self, api_key: str, base_url: str = GATEWAY_URL) -> None:
        # Initialize client with API key and base URL
        # CHAIN STEP 1: Validate API key format (fail-fast if invalid)
        if not api_key:
            raise ValueError("API key is required")
        if not api_key.startswith("rb_sk_"):
            raise ValueError("Invalid API key format - must start with 'rb_sk_'")
        
        # CHAIN STEP 2: Store configuration
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        
        # CHAIN STEP 3: Initialize HTTP client (let exceptions propagate)
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": f"rationalbloks-mcp/{__version__}"
            },
            timeout=60.0,
            follow_redirects=True
        )
    
    def execute(self, tool: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        # Execute MCP tool via gateway with automatic retry for transient failures
        # Returns: {"success": bool, "result": Any} or {"success": False, "error": str}
        # Retries ONLY transient failures (connect errors, timeouts, 503)
        # All other errors fail immediately (no silent fallbacks)
        payload = {"tool": tool, "arguments": arguments or {}}
        last_error = None
        
        # Retry loop for transient failures only
        for attempt in range(MAX_RETRIES):
            try:
                # CHAIN: Execute HTTP request
                response = self._client.post("/api/mcp/execute", json=payload)
                
                # CHAIN: Handle HTTP errors (fail-fast, no nested tries)
                if response.status_code == 401:
                    return {"success": False, "error": "Invalid API key. Get your key from https://rationalbloks.com/settings"}
                if response.status_code == 403:
                    return {"success": False, "error": "Permission denied. Your API key lacks the required scope."}
                if response.status_code == 429:
                    return {"success": False, "error": "Rate limit exceeded. Wait before making more requests."}
                if response.status_code == 400:
                    return {"success": False, "error": response.text or "Invalid request"}
                if response.status_code == 503:
                    # Service unavailable - retry
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (2 ** attempt))
                        continue
                    return {"success": False, "error": "Service temporarily unavailable. Try again later."}
                
                # Any other HTTP error - fail immediately
                response.raise_for_status()
                
                # CHAIN: Parse and return response
                return response.json()
            
            except httpx.ConnectError as e:
                # Network failure - retry
                last_error = f"Connection failed: {str(e)}"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))
                    continue
            
            except httpx.TimeoutException as e:
                # Timeout - retry
                last_error = f"Request timed out: {str(e)}"
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))
                    continue
            
            except Exception as e:
                # Unexpected error - fail immediately (no retry)
                return {"success": False, "error": f"Unexpected error: {type(e).__name__}: {str(e)}"}
        
        # All retries exhausted
        return {"success": False, "error": f"Max retries ({MAX_RETRIES}) exceeded. Last error: {last_error}"}
    
    def list_tools(self) -> dict[str, Any]:
        # Get available MCP tools from gateway (public endpoint)
        # Returns: {"tools": [...], "authentication": {...}}
        # Single try/except - if fails, return error dict
        try:
            response = self._client.get("/api/mcp/tools")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch tools: {str(e)}"}
    
    def health(self) -> dict[str, Any]:
        # Check MCP gateway health status
        # Returns: {"status": "healthy"} or {"status": "unreachable", "error": "..."}
        # Single try/except - if fails, return error dict
        try:
            response = self._client.get("/api/mcp/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}
    
    def close(self) -> None:
        # Close HTTP client and release resources (idempotent)
        if hasattr(self, '_client') and self._client is not None:
            self._client.close()
    
    def __enter__(self) -> "RationalBloksClient":
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
    
    def __del__(self) -> None:
        # Ensure cleanup on garbage collection (suppress all exceptions)
        try:
            self.close()
        except Exception:
            pass
