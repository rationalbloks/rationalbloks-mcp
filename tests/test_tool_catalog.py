# ============================================================================
# TOOL CATALOG — what the package itself writes about the tools
# ============================================================================
# The tools are LogicBlok's (logicblok/mcp_gateway.py, THE TOOLS): its tests hold each
# tool's hints, arguments and description length. The package writes two things of its
# own: the server instructions every client keeps on connect, and the API reference
# resource, written from the catalog the gateway serves. Claude Code keeps the first
# 2048 characters of the server instructions, so text past that never reaches the agent.
# ============================================================================

from rationalbloks_mcp.backend import BackendMCPServer
from rationalbloks_mcp.backend.server import api_reference

# What Claude Code keeps of the server instructions
CLAUDE_CODE_TEXT_LIMIT = 2048


def tool(name: str, group: str, read: bool, destructive: bool = False) -> dict:
    # One tool as the gateway serves it
    return {"name": name, "group": group,
            "annotations": {"readOnlyHint": read, "destructiveHint": destructive, "idempotentHint": read, "openWorldHint": False}}


CATALOG = [tool("list_projects", "Relational Tools", True), tool("deploy_staging", "Relational Tools", False),
           tool("delete_project", "Relational Tools", False, destructive=True),
           tool("traverse_graph", "Graph Data Tools", True), tool("delete_module", "Module Tools", False, destructive=True)]


def test_the_api_reference_lists_every_tool_once_in_its_group_under_its_kind():
    assert api_reference(CATALOG).splitlines()[2:] == [
        "Read tools only read. Write tools never lose data. Destructive tools can, and declare destructiveHint.",
        "",
        "## Relational Tools",
        "- Read: list_projects",
        "- Write: deploy_staging",
        "- Destructive: delete_project",
        "",
        "## Graph Data Tools",
        "- Read: traverse_graph",
        "",
        "## Module Tools",
        "- Destructive: delete_module",
        "",
        "For full documentation, visit https://rationalbloks.com/documentation",
    ]


def test_the_instructions_fit_what_claude_code_keeps():
    assert len(BackendMCPServer.INSTRUCTIONS) <= CLAUDE_CODE_TEXT_LIMIT
