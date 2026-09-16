# ============================================================================
# CLIENT ERRORS — a failed tool call carries LogicBlok's detail
# ============================================================================
# The gateway answers a failed call with an HTTP error whose detail says what to do: a
# missing argument, a busy project naming its running job, a plan that drops data. The
# client raises with that detail, so the agent reads it instead of a bare status line.
# ============================================================================

import asyncio

import httpx
import pytest

from rationalbloks_mcp.backend.client import LogicBlokClient


def answering(status_code: int, **response) -> LogicBlokClient:
    # A client whose gateway always gives this answer
    client = LogicBlokClient("rb_sk_" + "0" * 40)
    client._client = httpx.AsyncClient(base_url="https://gateway.test", transport=httpx.MockTransport(
        lambda request: httpx.Response(status_code, **response)))
    return client


def test_a_refusal_raises_with_the_gateway_detail():
    detail = "Another operation on this project is running (promote_database_project, job 1f0c). Try again when it has finished."
    client = answering(409, json={"detail": detail})
    with pytest.raises(Exception) as refused:
        asyncio.run(client.execute("deploy_staging", {"project_id": "p1"}))
    assert str(refused.value) == f"RationalBloks answered 409 to deploy_staging: {detail}"


def test_a_non_json_failure_raises_with_its_text():
    client = answering(502, text="Bad gateway")
    with pytest.raises(Exception) as failed:
        asyncio.run(client.execute("list_projects"))
    assert str(failed.value) == "RationalBloks answered 502 to list_projects: Bad gateway"


def test_a_result_is_returned():
    client = answering(200, json={"success": True, "result": {"projects": [], "total": 0}})
    assert asyncio.run(client.execute("list_projects")) == {"projects": [], "total": 0}
