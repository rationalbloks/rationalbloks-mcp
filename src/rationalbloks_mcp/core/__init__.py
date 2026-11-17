# ============================================================================
# RATIONALBLOKS MCP - CORE MODULE
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# The server's plumbing: the transport layer (STDIO + HTTP) and the API key utilities. The server itself
# is backend/server.py.
# ============================================================================

from .auth import (
    is_api_key,
    stdio_api_key,
    extract_api_key_from_request,
)
from .transport import (
    run_stdio,
    run_http,
    create_http_app,
)

__all__ = [
    # Auth
    "is_api_key",
    "stdio_api_key",
    "extract_api_key_from_request",
    # Transport
    "run_stdio",
    "run_http",
    "create_http_app",
]
