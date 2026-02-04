# ============================================================================
# RATIONALBLOKS MCP - FRONTEND MODULE (THIN LAYER)
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# THE PHILOSOPHY:
# This MCP is a THIN LAYER that provides guardrails, not generation.
# The AI agent (Claude) does the creative work. The MCP ensures the AI
# follows THE ONE WAY architecture using frontblok-auth + frontblok-crud.
#
# 6 TOOLS ONLY:
#
# 📖 TEACH:
#   - get_frontend_guidelines: THE ONE WAY architecture + coding rules
#   - get_template_structure: Explore rationalbloksfront template
#
# 🔧 BOOTSTRAP (one-time setup):
#   - clone_template: Fresh project from GitHub
#   - generate_types: TypeScript interfaces from schema
#   - generate_api_service: datablokApi.ts (THE ONE WAY glue)
#   - configure_api_url: Set .env API URL
#
# THE AI WRITES ALL VIEWS, FORMS, AND CUSTOM UI.
# ============================================================================

from .client import FrontendClient
from .tools import (
    FRONTEND_TOOLS,
    FRONTEND_PROMPTS,
    FrontendMCPServer,
    create_frontend_server,
)

__all__ = [
    "FrontendClient",
    "FRONTEND_TOOLS",
    "FRONTEND_PROMPTS",
    "FrontendMCPServer",
    "create_frontend_server",
]

