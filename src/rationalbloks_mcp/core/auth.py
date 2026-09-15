# ============================================================================
# RATIONALBLOKS MCP - AUTHENTICATION UTILITIES
# ============================================================================
# Copyright 2026 RationalBloks. All Rights Reserved.
#
# The API key rules of the MCP server. Over HTTP a key travels as a Bearer token (RFC 6750
# header format); over STDIO it is read from RATIONALBLOKS_API_KEY. LogicBlok verifies the key
# on every call; this module only checks its shape.
#
# CHAIN MANTRA ENFORCEMENT:
# - One format rule (is_api_key) for both transports
# - A missing or malformed STDIO key raises at startup, with the remedy in the message
# ============================================================================

from starlette.requests import Request

# Public API
__all__ = [
    "is_api_key",
    "require_api_key",
    "extract_api_key_from_request",
]

# API key prefix - all RationalBloks keys start with this
API_KEY_PREFIX = "rb_sk_"
BEARER_PREFIX = "Bearer "
# The prefix plus at least 20 characters
API_KEY_MIN_LENGTH = len(API_KEY_PREFIX) + 20


def is_api_key(value: object) -> bool:
    # Whether value has the shape of a RationalBloks API key
    return isinstance(value, str) and value.startswith(API_KEY_PREFIX) and len(value) >= API_KEY_MIN_LENGTH


def require_api_key(api_key: str | None) -> str:
    # The STDIO key, or ValueError naming what is wrong and how to fix it
    if not api_key:
        raise ValueError(
            "RATIONALBLOKS_API_KEY environment variable not set. Get your API key from "
            "https://rationalbloks.com/settings, then: export RATIONALBLOKS_API_KEY=rb_sk_your_key_here"
        )
    if not is_api_key(api_key):
        raise ValueError(
            f"Invalid API key format: a RationalBloks key starts with '{API_KEY_PREFIX}' and has at "
            f"least {API_KEY_MIN_LENGTH} characters"
        )
    return api_key


def extract_api_key_from_request(request: Request) -> str | None:
    # The API key in the request's Authorization header (Bearer rb_sk_...), or None when the
    # header is absent or does not carry a key
    if request is None:
        return None

    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith(BEARER_PREFIX):
        return None

    api_key = auth_header[len(BEARER_PREFIX):]
    return api_key if is_api_key(api_key) else None
