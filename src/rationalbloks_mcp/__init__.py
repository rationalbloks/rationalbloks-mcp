# ============================================================================
# RATIONALBLOKS MCP - Backend API Server
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Deploy production REST APIs and Neo4j Graph APIs in minutes. 44 tools for:
#   - Relational: 18 tools (create, list, deploy, rollback, templates, etc.)
#   - Graph Schema: 11 tools (create, deploy, rollback, templates, etc.)
#   - Graph Data: 15 tools (CRUD, search, traverse, bulk, fulltext)
#
# Usage:
#   export RATIONALBLOKS_API_KEY=rb_sk_your_key_here
#   rationalbloks-mcp
#
# For frontend, use our NPM packages:
#   npm install @rationalbloks/frontblok-auth @rationalbloks/frontblok-crud
#
# Environment Variables:
#   RATIONALBLOKS_API_KEY - Your API key (required for STDIO mode)
#   TRANSPORT             - Transport: stdio (default) or http
# ============================================================================

import os
import sys

# Version from package metadata
from importlib.metadata import version as _get_version
__version__ = _get_version("rationalbloks-mcp")

# Public API
__all__ = [
    "__version__",
    "main",
    "BACKEND_TOOLS",
    "GRAPH_TOOLS",
    "GRAPH_DATA_TOOLS",
    "INFRASTRUCTURE_TOOLS",
]

# Re-export for convenience
from .backend.tools import (
    BACKEND_TOOLS, GRAPH_TOOLS, GRAPH_DATA_TOOLS,
    INFRASTRUCTURE_TOOLS,
)


def _validate_api_key(api_key: str | None, transport: str) -> str | None:
    # Validate API key for the given transport
    # HTTP mode: API key provided per-request (returns None)
    # STDIO mode: API key required at startup (returns validated key)
    
    # HTTP mode: API key provided per-request
    if transport == "http":
        return None
    
    # STDIO mode: API key required at startup
    if not api_key:
        print("ERROR: RATIONALBLOKS_API_KEY environment variable not set", file=sys.stderr)
        print("", file=sys.stderr)
        print("Get your API key from: https://rationalbloks.com/settings", file=sys.stderr)
        print("", file=sys.stderr)
        print("Then set it:", file=sys.stderr)
        print("  export RATIONALBLOKS_API_KEY=rb_sk_your_key_here", file=sys.stderr)
        sys.exit(1)
    
    if not api_key.startswith("rb_sk_"):
        print("ERROR: Invalid API key format. Must start with 'rb_sk_'", file=sys.stderr)
        sys.exit(1)
    
    return api_key


def main() -> None:
    # Main entry point - runs the backend MCP server
    api_key = os.environ.get("RATIONALBLOKS_API_KEY")
    transport = os.environ.get("TRANSPORT", "stdio").lower()
    http_mode = transport == "http"
    
    # Validate API key
    validated_key = _validate_api_key(api_key, transport)
    
    print(f"[rationalbloks-mcp] Starting server (44 tools: 18 relational + 11 graph schema + 15 graph data)...", file=sys.stderr)
    
    try:
        from .backend import create_backend_server
        server = create_backend_server(api_key=validated_key, http_mode=http_mode)
        server.run(transport=transport)
        
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
