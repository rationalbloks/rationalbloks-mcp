# ============================================================================
# RATIONALBLOKS MCP - Backend API Server
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Deploy production REST APIs and Neo4j Graph APIs in minutes. 48 tools for:
#   - Relational: 22 tools (create, list, deploy, rollback, templates, storage, schema reference, etc.)
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
import traceback

# Version from package metadata, via _version.py. Read from there rather than
# assigned here, so backend/tools.py can import it without importing this package
# back and creating a cycle that only works if the assignment stays above line 42.
from ._version import __version__

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
    INFRASTRUCTURE_TOOLS, create_backend_server,
)


def main() -> None:
    # Main entry point - runs the backend MCP server. Over STDIO the key is checked when the
    # server is built (core.auth.require_api_key); over HTTP each request carries its own key.
    transport = os.environ.get("TRANSPORT", "stdio").lower()
    http_mode = transport == "http"
    api_key = None if http_mode else os.environ.get("RATIONALBLOKS_API_KEY")

    print("[rationalbloks-mcp] Starting server (48 tools: 22 relational + 11 graph schema + 15 graph data)...", file=sys.stderr)

    try:
        server = create_backend_server(api_key=api_key, http_mode=http_mode)
        server.run(transport=transport)

    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        # Surface the exception CLASS — the most diagnostic part — and, under
        # RATIONALBLOKS_DEBUG, the full traceback. A bare str(e) at the top-level
        # entry point hid WHERE and WHY startup failed (chain-of-events: fail loud).
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        if os.environ.get("RATIONALBLOKS_DEBUG"):
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
