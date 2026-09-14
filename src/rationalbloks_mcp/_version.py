# ============================================================================
# RATIONALBLOKS MCP - VERSION
# ============================================================================
# The single place the package version is read, in a module that imports nothing
# from this package. Both __init__.py and backend/tools.py read it from here, so
# neither has to import the other and there is no cycle to order correctly.
# ============================================================================

from importlib.metadata import version as _get_version

__version__ = _get_version("rationalbloks-mcp")
