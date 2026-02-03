# ============================================================================
# RATIONALBLOKS MCP - CORE MODULE
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Shared core components for Backend and Frontend MCP modes.
# This module contains:
#   - Base MCP server class
#   - Transport layer (STDIO + HTTP)
#   - Authentication utilities
#
# ARCHITECTURE:
# Both Backend and Frontend modes extend this core.
# No duplication of server, transport, or auth logic.
# ============================================================================

from .auth import (
    validate_api_key,
    extract_api_key_from_request,
    APIKeyCache,
)
from .transport import (
    run_stdio,
    run_http,
    create_http_app,
)
from .server import (
    BaseMCPServer,
    create_mcp_server,
)

__all__ = [
    # Auth
    "validate_api_key",
    "extract_api_key_from_request",
    "APIKeyCache",
    # Transport
    "run_stdio",
    "run_http",
    "create_http_app",
    # Server
    "BaseMCPServer",
    "create_mcp_server",
]
