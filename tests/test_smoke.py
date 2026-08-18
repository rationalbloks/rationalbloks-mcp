# ============================================================================
# SMOKE TEST — server construction registers all tools
# ============================================================================
# Guards the 0.10.2 failure class, which unit tests cannot see: an SDK dependency
# (mcp) ships a major that removes the handler-registration API this package
# builds on, so the server raises at construction and serves zero tools.
# Constructing the server runs that exact path; a non-empty tool registry proves
# the handlers wired up. A format-valid dummy key satisfies startup validation —
# no backend call is made (tools/list is served from the local registry).
# ============================================================================

from rationalbloks_mcp.backend import create_backend_server

# rb_sk_ + >=20 chars: passes startup format validation without a real backend.
_DUMMY_API_KEY = "rb_sk_" + "0" * 40


def test_server_constructs_and_registers_tools():
    # On an incompatible SDK this call raises inside setup_handlers() — the exact
    # crash that shipped in 0.10.2 — and the test fails before the assert.
    server = create_backend_server(api_key=_DUMMY_API_KEY, http_mode=False)
    assert server._tools, "server registered no tools"
