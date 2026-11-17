# ============================================================================
# SMOKE TEST — server construction wires every handler
# ============================================================================
# Guards the 0.10.2 failure class, which unit tests cannot see: an SDK dependency
# (mcp) ships a major that removes the handler-registration API this package
# builds on, so the server raises at construction and serves nothing.
# Constructing the server runs that exact path. A format-valid dummy key satisfies
# startup validation; no backend call is made (the tools are listed from the
# gateway only when a client asks).
# ============================================================================

from rationalbloks_mcp.backend import create_backend_server

# rb_sk_ + >=20 chars: passes startup format validation without a real backend.
_DUMMY_API_KEY = "rb_sk_" + "0" * 40


def test_server_constructs_with_every_handler_and_its_prompts():
    # On an incompatible SDK this call raises inside the server's construction — the exact
    # crash that shipped in 0.10.2 — and the test fails before the asserts.
    server = create_backend_server(api_key=_DUMMY_API_KEY, http_mode=False)
    assert set(server._build_handlers()) == {"on_list_tools", "on_call_tool", "on_list_prompts", "on_get_prompt",
                                             "on_list_resources", "on_read_resource"}
    assert [prompt.name for prompt in server._prompts] == [
        "create-project-from-description", "fix-schema-errors", "create-graph-project-from-description"]
