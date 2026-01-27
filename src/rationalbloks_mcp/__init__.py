# ============================================================================
# RATIONALBLOKS MCP - Main Entry Point
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Connect AI agents (Claude, GPT, Cursor) to RationalBloks projects
#
# Usage:
#   export RATIONALBLOKS_API_KEY=rb_sk_your_key_here
#   rationalbloks-mcp
#
# Environment Variables (Required):
#   RATIONALBLOKS_API_KEY - Your API key (required for STDIO mode)
#
# Environment Variables (Optional):
#   TRANSPORT - "stdio" (default) or "http"
#   RATIONALBLOKS_BASE_URL - API Gateway URL (default: https://logicblok.rationalbloks.com)
#   RATIONALBLOKS_TIMEOUT - Request timeout in seconds (default: 30)
#   RATIONALBLOKS_LOG_LEVEL - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
# ============================================================================

import os
import sys

from .server import RationalBloksMCPServer
from .client import RationalBloksClient
from .tools import TOOLS

# ============================================================================
# VERSION - Single Source of Truth (Chain Mantra)
# ============================================================================
# Read from pyproject.toml via importlib.metadata
# If this fails, the package is not installed correctly - fail immediately
# NO FALLBACKS - there is only ONE correct path
from importlib.metadata import version as _get_version
__version__ = _get_version("rationalbloks-mcp")

__author__ = "RationalBloks"
__all__ = ["RationalBloksMCPServer", "RationalBloksClient", "TOOLS", "main", "__version__"]


def main() -> None:
    # Entry point for rationalbloks-mcp command
    # Supports two modes:
    #   - stdio: Local IDE integration (Claude Desktop, VS Code, Cursor)
    #   - http: Cloud deployment (Smithery, Replit, web agents)
    api_key = os.environ.get("RATIONALBLOKS_API_KEY")
    transport = os.environ.get("TRANSPORT", "stdio").lower()
    
    # HTTP mode: API key provided per-request via Authorization header
    if transport == "http":
        try:
            server = RationalBloksMCPServer(api_key=api_key, http_mode=True)
            server.run(transport="http")
        except KeyboardInterrupt:
            sys.exit(0)
        return
    
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
    
    # CHAIN: Run STDIO server (single path, fail-fast)
    try:
        server = RationalBloksMCPServer(api_key=api_key)
        server.run(transport=transport)
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
