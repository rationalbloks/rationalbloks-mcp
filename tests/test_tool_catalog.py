# ============================================================================
# TOOL CATALOG — the rules every tool's listing keeps
# ============================================================================
# A client decides from a tool's listing alone whether to ask before calling it, so the
# listing carries the risk: readOnlyHint on the tools that only read, destructiveHint on
# exactly the tools that can lose data, openWorldHint false on all (each reaches the
# caller's RationalBloks account alone). Claude Code keeps the first 2048 characters of a
# tool description and of the server instructions, so text past that never reaches the
# agent. The LogicBlok tests pin the other half: each tool's arguments and its read or
# write scope against the gateway's registry.
# ============================================================================

from rationalbloks_mcp.backend import INFRASTRUCTURE_TOOLS, BackendMCPServer
from rationalbloks_mcp.backend.tools import api_reference

HINTS = {"readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"}

# The tools that can lose data. Changing this set changes what a client asks before running.
DESTRUCTIVE = {
    "update_schema", "drop_schema_items", "deploy_destructive", "rollback_project", "delete_project",
    "update_graph_schema", "rollback_graph_project", "delete_graph_project",
    "delete_graph_node", "delete_graph_relationship",
    "set_module_env", "delete_module",
}

# What Claude Code keeps of a tool description and of the server instructions
CLAUDE_CODE_TEXT_LIMIT = 2048

# The read-only allow rules the docs give: mcp__rationalbloks__get_*, mcp__rationalbloks__list_* and these names
READ_PREFIXES = ("get_", "list_")
READ_NAMES = {"search_graph_nodes", "fulltext_search_graph", "traverse_graph", "preview_schema_change"}


def test_every_tool_states_all_four_hints():
    for tool in INFRASTRUCTURE_TOOLS:
        hints = tool["annotations"]
        assert set(hints) == HINTS, f"{tool['name']} states {sorted(hints)}"
        assert all(isinstance(value, bool) for value in hints.values()), tool["name"]


def test_destructive_hint_marks_exactly_the_tools_that_can_lose_data():
    marked = {tool["name"] for tool in INFRASTRUCTURE_TOOLS if tool["annotations"]["destructiveHint"]}
    assert marked == DESTRUCTIVE


def test_no_read_tool_is_destructive_and_no_tool_is_open_world():
    for tool in INFRASTRUCTURE_TOOLS:
        hints = tool["annotations"]
        assert not (hints["readOnlyHint"] and hints["destructiveHint"]), tool["name"]
        assert hints["openWorldHint"] is False, tool["name"]


def test_tool_names_are_unique():
    names = [tool["name"] for tool in INFRASTRUCTURE_TOOLS]
    assert len(names) == len(set(names))


def test_the_documented_read_patterns_match_exactly_the_read_tools():
    # The README and the IDE Setup page offer these Claude Code allow rules as "every read tool, and no
    # other"; a new tool named get_ or list_ that writes, or a read tool outside them, breaks that claim
    matched = {tool["name"] for tool in INFRASTRUCTURE_TOOLS
               if tool["name"].startswith(READ_PREFIXES) or tool["name"] in READ_NAMES}
    reads = {tool["name"] for tool in INFRASTRUCTURE_TOOLS if tool["annotations"]["readOnlyHint"]}
    assert matched == reads


def test_the_api_reference_lists_every_tool_once():
    listed = []
    for line in api_reference().splitlines():
        if line.startswith("- "):
            listed += line.split(": ", 1)[1].split(", ")
    assert sorted(listed) == sorted(tool["name"] for tool in INFRASTRUCTURE_TOOLS)


def test_descriptions_and_instructions_fit_what_claude_code_keeps():
    for tool in INFRASTRUCTURE_TOOLS:
        assert len(tool["description"]) <= CLAUDE_CODE_TEXT_LIMIT, (
            f"{tool['name']}: {len(tool['description'])} characters")
    assert len(BackendMCPServer.INSTRUCTIONS) <= CLAUDE_CODE_TEXT_LIMIT
