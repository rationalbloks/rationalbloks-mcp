# ============================================================================
# RATIONALBLOKS MCP - FRONTEND MODULE
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# Frontend mode provides 14 tools using THE ONE WAY ARCHITECTURE:
# - @rationalbloks/universalfront: createAuthApi for auth + tokens
# - @rationalbloks/frontbuilderblok: initApi + getApi for generic CRUD
#
# GENERATION TOOLS (work on any existing project):
# - generate_types: TypeScript interfaces from schema
# - generate_api_service: THE ONE WAY pattern (createAuthApi + initApi + ENTITIES)
# - generate_entity_view: List view using getApi().getAll()
# - generate_entity_form: Create/edit form using getApi().create/update()
# - generate_all_views: All views for all entities
# - generate_dashboard: Dashboard with stats using getApi()
# - update_routes: Wire up routes in App.tsx
# - update_navbar: Update navigation links
#
# SCAFFOLD TOOLS:
# - scaffold_frontend: Apply ALL generators to existing project
# - create_app: Full automation (clone + backend + scaffold)
#
# UTILITY TOOLS:
# - clone_template: Clone rationalbloksfront template
# - configure_api_url: Set API URL in frontend .env
# - create_backend: Create backend via Backend MCP
# - get_template_structure: Explore template file structure
# ============================================================================

from .client import FrontendClient
from .app_generator import AppGenerator
from .tools import (
    FRONTEND_TOOLS,
    FRONTEND_PROMPTS,
    FrontendMCPServer,
    create_frontend_server,
)

__all__ = [
    "AppGenerator",
    "FrontendClient",
    "FRONTEND_TOOLS",
    "FRONTEND_PROMPTS",
    "FrontendMCPServer",
    "create_frontend_server",
]
