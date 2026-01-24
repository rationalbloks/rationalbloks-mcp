# RationalBloks MCP Server
# Copyright © 2026 RationalBloks. All Rights Reserved.
#
# Connect AI agents (Claude, GPT, Cursor) to your RationalBloks projects
#
# Usage:
#   export RATIONALBLOKS_API_KEY=rb_sk_your_key_here
#   rationalbloks-mcp

import os
import sys

from .server import RationalBloksMCPServer
from .client import RationalBloksClient
from .tools import TOOLS

__version__ = "0.1.0"
__author__ = "RationalBloks"
__all__ = ["RationalBloksMCPServer", "RationalBloksClient", "TOOLS", "main"]


def main():
    """Entry point for the rationalbloks-mcp command.
    
    Supports two modes:
    - stdio (default): For local use with Claude Desktop, VS Code, Cursor
    - http: For Smithery/cloud deployment (set TRANSPORT=http)
    """
    api_key = os.environ.get("RATIONALBLOKS_API_KEY")
    transport = os.environ.get("TRANSPORT", "stdio").lower()
    
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
    
    try:
        server = RationalBloksMCPServer(api_key=api_key)
        server.run(transport=transport)
    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
