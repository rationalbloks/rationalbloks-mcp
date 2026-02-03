# ============================================================================
# RATIONALBLOKS MCP - AUTHENTICATION UTILITIES
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Shared authentication logic for Backend and Frontend MCP modes.
# Follows OAuth2 Bearer Token pattern (RFC 6750).
#
# CHAIN MANTRA ENFORCEMENT:
# - Single validation path - if key is invalid, fail immediately
# - No silent fallbacks - explicit error messages
# - Caching for performance (per-session, not persistent)
# ============================================================================

from typing import Any
from starlette.requests import Request

# Public API
__all__ = [
    "validate_api_key",
    "extract_api_key_from_request",
    "APIKeyCache",
]

# API key prefix - all RationalBloks keys start with this
API_KEY_PREFIX = "rb_sk_"
BEARER_PREFIX = "Bearer "


def validate_api_key(api_key: str | None) -> tuple[bool, str | None]:
    # Validate API key format
    # Returns: (is_valid: bool, error_message: str | None)
    # CHAIN MANTRA: Single validation path, explicit errors
    if not api_key:
        return False, "API key is required"
    
    if not isinstance(api_key, str):
        return False, "API key must be a string"
    
    if not api_key.startswith(API_KEY_PREFIX):
        return False, f"Invalid API key format - must start with '{API_KEY_PREFIX}'"
    
    # Minimum length check (prefix + at least 20 chars)
    if len(api_key) < len(API_KEY_PREFIX) + 20:
        return False, "API key is too short"
    
    return True, None


def extract_api_key_from_request(request: Request) -> str | None:
    # Extract API key from HTTP Authorization header
    # Expected format: Authorization: Bearer rb_sk_...
    # Returns: API key string or None if not found/invalid
    if request is None:
        return None
    
    auth_header = request.headers.get("authorization", "")
    
    if not auth_header.startswith(BEARER_PREFIX):
        return None
    
    api_key = auth_header[len(BEARER_PREFIX):]
    
    # Validate format (don't validate against server yet)
    is_valid, _ = validate_api_key(api_key)
    if not is_valid:
        return None
    
    return api_key


class APIKeyCache:
    # In-memory cache for validated API keys
    # Stores validation results to avoid repeated calls to auth server
    # Cache is per-server-instance (not persistent across restarts)
    # SECURITY:
    # - Only stores key prefix (first 20 chars) as cache key
    # - Full key never stored in cache
    # - Cache cleared on server restart
    
    def __init__(self, max_size: int = 100) -> None:
        # Initialize cache with maximum size
        self._cache: dict[str, dict[str, Any]] = {}
        self._max_size = max_size
    
    def _get_cache_key(self, api_key: str) -> str:
        # Get cache key from API key (uses prefix only for security)
        return api_key[:20] if len(api_key) >= 20 else api_key
    
    def get(self, api_key: str) -> dict[str, Any] | None:
        # Get cached user info for API key
        cache_key = self._get_cache_key(api_key)
        return self._cache.get(cache_key)
    
    def set(self, api_key: str, user_info: dict[str, Any]) -> None:
        # Cache user info for API key
        # Evict oldest entries if cache is full
        if len(self._cache) >= self._max_size:
            # Simple eviction: clear half the cache
            keys_to_remove = list(self._cache.keys())[:self._max_size // 2]
            for key in keys_to_remove:
                del self._cache[key]
        
        cache_key = self._get_cache_key(api_key)
        self._cache[cache_key] = user_info
    
    def clear(self) -> None:
        # Clear all cached entries
        self._cache.clear()
    
    def __len__(self) -> int:
        # Return number of cached entries
        return len(self._cache)
