#!/usr/bin/env python3
# ============================================================================
# RATIONALBLOKS MCP - RELEASE
# ============================================================================
# Publishes this package to the two public channels that serve it:
#   PyPI          - what `uvx rationalbloks-mcp` downloads (Claude Desktop, Smithery)
#   MCP Registry  - where MCP clients discover the server
#
# The hosted server at mcp.rationalbloks.com is NOT released here. It is built from
# GitHub by rationalbloks-mcp-infra/deploy.py and driven by deploy_all.py, so a deploy
# and a release are separate acts serving separate audiences. Deploying does not
# publish, and publishing does not deploy.
#
# WHY THIS FILE EXISTS:
# Both channels were updated by hand and both fell behind without anyone noticing.
# PyPI sat three fixes stale; the registry sat seven months and five releases stale,
# telling every client to install a version that predated most of the product. The
# fleet never rots this way because deploy_all.py stamps and compares every box, so
# this file gives the packages the same treatment: one command, and a drift row in
# `deploy_all.py status` that makes falling behind visible.
#
# CHAIN OF EVENTS:
# Every step raises on failure and nothing is transmitted until every preflight has
# passed. PyPI refuses to overwrite a version that already exists, so a release that
# uploads and then fails cannot be retried without a version bump. That is precisely
# why all verification runs first and the two uploads run last.
#
# IDEMPOTENT PER CHANNEL:
# What each index already serves is read BEFORE anything is verified, built or sent,
# and a channel that already carries this version is skipped. When both carry it there
# is nothing to release and the run ends there: no test run, no publisher download,
# and above all no interactive login. That is what lets this sit at the FRONT of
# `deploy_all.py all` and cost two HTTP reads on every deploy with nothing to publish.
#
# USAGE:
#   python release.py           # publish whatever the two channels are missing
#   python release.py status    # read-only: what each channel serves, no side effects
# ============================================================================

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

REPO = Path(__file__).resolve().parent

# The operator's secret store: the same folder deploy_all.py reads its .pem files
# from. The token is never printed, echoed, or written anywhere by this script.
PYPI_TOKEN_FILE = Path(
    r"C:\Users\velos\OneDrive\RATIONALBLOKS\01_RELATIONAL_DATABLOK\00_CYBER_CRITICAL"
    r"\PYPI_TOKEN_RATIONALBLOKS.txt"
)

PACKAGE_NAME = "rationalbloks-mcp"
SERVER_NAME = "io.github.rationalbloks/rationalbloks-mcp"

PYPI_JSON_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
REGISTRY_SEARCH_URL = "https://registry.modelcontextprotocol.io/v0.1/servers?search=rationalbloks"
SCHEMA_URL = "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"

# The registry rejects a description longer than this with HTTP 422. The published
# JSON schema does not declare the limit, so it is enforced here from the registry's
# own observed behaviour rather than read from the schema.
DESCRIPTION_MAX = 100

PUBLISHER_EXE = REPO / ("mcp-publisher.exe" if os.name == "nt" else "mcp-publisher")
PUBLISHER_URL = (
    "https://github.com/modelcontextprotocol/registry/releases/latest/download/"
    "mcp-publisher_{platform}_{arch}.tar.gz"
)

# Both indexes are eventually consistent, so the final verification polls rather than
# reading once. 20 attempts at 15s covers the few minutes PyPI can take to serve a
# fresh upload from its JSON API.
VERIFY_ATTEMPTS = 20
VERIFY_INTERVAL = 15


# ============================================================================
# HELPERS
# ============================================================================

def run(argv, capture=False, secret=None):
    # Run a command in the repo and raise on any non-zero exit, so one failed step
    # halts the release. `secret`, when given, is masked in the echoed command line.
    shown = " ".join(argv)
    if secret:
        shown = shown.replace(secret, "***")
    print(f"    > {shown}")
    result = subprocess.run(argv, cwd=REPO, capture_output=capture, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip() if capture else ""
        raise RuntimeError(f"command failed (exit {result.returncode}): {shown}\n{detail}")
    return result.stdout.strip() if capture else ""


def get_json(url):
    # Read a JSON document. Raises on transport or parse failure: a release must never
    # continue on a guess about what an index currently holds.
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def step(message):
    print(f"\n  {message}")


def ok(message):
    print(f"    OK  {message}")


# ============================================================================
# VERSION SOURCES
# ============================================================================
# One release number lives in four places. They must agree before anything ships: the
# registry rejects an entry whose version does not match its PyPI package exactly, and
# a mismatch inside server.json publishes a server entry pointing at a package version
# that was never uploaded.

def read_pyproject_version():
    # pyproject.toml is the source of truth; every other file must match it.
    text = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', text, re.M)
    if not match:
        raise RuntimeError("pyproject.toml declares no [project] version")
    return match.group(1)


def read_smithery_version():
    text = (REPO / "smithery.yaml").read_text(encoding="utf-8")
    match = re.search(r"^version: (.+)$", text, re.M)
    if not match:
        raise RuntimeError("smithery.yaml declares no version")
    return match.group(1).strip()


def read_server_json():
    return json.loads((REPO / "server.json").read_text(encoding="utf-8"))


# ============================================================================
# PREFLIGHT
# ============================================================================
# verify_manifests runs first and always, because it yields the version every other
# check is measured against. The rest are gathered into preflight() at the end of this
# section and run only when a channel is actually missing that version.

def verify_manifests():
    # Every field the registry validates, checked before it can reject the upload.
    step("Verifying manifests")
    version = read_pyproject_version()
    server = read_server_json()

    if server.get("$schema") != SCHEMA_URL:
        raise RuntimeError(f"server.json $schema must be {SCHEMA_URL}")

    if server.get("name") != SERVER_NAME:
        raise RuntimeError(f"server.json name must be {SERVER_NAME}")

    description = server.get("description", "")
    if len(description) > DESCRIPTION_MAX:
        raise RuntimeError(
            f"server.json description is {len(description)} characters; the registry "
            f"rejects anything over {DESCRIPTION_MAX} with HTTP 422"
        )

    packages = server.get("packages") or []
    if len(packages) != 1:
        raise RuntimeError("server.json must declare exactly one package")

    found = {
        "pyproject.toml":       version,
        "server.json":          server.get("version"),
        "server.json package":  packages[0].get("version"),
        "smithery.yaml":        read_smithery_version(),
    }
    disagreeing = {name: value for name, value in found.items() if value != version}
    if disagreeing:
        raise RuntimeError(
            f"version disagreement, pyproject.toml says {version}: "
            + ", ".join(f"{name}={value}" for name, value in disagreeing.items())
        )

    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    if f'mcpName = "{SERVER_NAME}"' not in pyproject:
        raise RuntimeError(f"pyproject.toml must carry mcpName = \"{SERVER_NAME}\"")

    readme = (REPO / "README.md").read_text(encoding="utf-8")
    if f"<!-- mcp-name: {SERVER_NAME} -->" not in readme:
        raise RuntimeError(f"README.md must carry the <!-- mcp-name: {SERVER_NAME} --> tag")

    ok(f"version {version} agrees across all four manifests")
    ok(f"description is {len(description)}/{DESCRIPTION_MAX} characters")
    return version


def verify_working_tree():
    # A release must be reproducible from origin/main, so nothing uncommitted and
    # nothing unpushed may enter it.
    step("Verifying working tree")
    dirty = run(["git", "status", "--porcelain"], capture=True)
    if dirty:
        raise RuntimeError(f"working tree is not clean:\n{dirty}")

    run(["git", "fetch", "--quiet", "origin", "main"])
    head = run(["git", "rev-parse", "HEAD"], capture=True)
    remote = run(["git", "rev-parse", "origin/main"], capture=True)
    if head != remote:
        raise RuntimeError(f"HEAD {head[:12]} is not origin/main {remote[:12]}; push first")

    ok(f"clean and level with origin/main at {head[:12]}")


def verify_tests():
    # The published artifact is built from this tree, so the tree's tests gate it.
    step("Running tests")
    run(["uv", "run", "--with", "pytest", "--with", "pytest-asyncio", "pytest", "tests/", "-q"])
    ok("tests pass")


def read_channel_state(version):
    # What each index already serves. The release is idempotent per channel: a channel
    # that already carries this version is skipped rather than re-published, so running
    # this on every deploy is safe and a repeat run does nothing.
    #
    # PyPI versions are immutable, so a skip there is not a nicety but the only correct
    # behaviour. It is announced rather than silent: if this tree has changes that were
    # never released, the version was not bumped, and the message says so.
    step("Reading what each channel already serves")
    on_pypi = version in get_json(PYPI_JSON_URL).get("releases", {})
    on_registry = read_registry_version() == version

    if on_pypi:
        ok(f"PyPI already serves {version}, skipping "
           f"(bump the version if this tree has changes to publish)")
    else:
        ok(f"PyPI does not have {version} yet")

    if on_registry:
        ok(f"the MCP Registry already serves {version}, skipping")
    else:
        ok(f"the MCP Registry does not have {version} yet")

    return on_pypi, on_registry


def verify_publisher_present():
    # Fetched during preflight, never between the two uploads: a missing binary
    # discovered after the PyPI upload would strand the release half-published.
    step("Checking the MCP registry publisher")
    if PUBLISHER_EXE.exists():
        ok(f"{PUBLISHER_EXE.name} already present")
        return

    system = "windows" if os.name == "nt" else platform.system().lower()
    arch = "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "amd64"
    url = PUBLISHER_URL.format(platform=system, arch=arch)
    archive = REPO / "mcp-publisher.tar.gz"

    print(f"    > downloading {url}")
    urllib.request.urlretrieve(url, archive)
    run(["tar", "xf", archive.name, PUBLISHER_EXE.name])
    archive.unlink()

    if not PUBLISHER_EXE.exists():
        raise RuntimeError(f"{PUBLISHER_EXE.name} missing after extraction")
    ok(f"{PUBLISHER_EXE.name} downloaded")


def verify_server_json():
    # The publisher's own validator, run against the live registry. It is the authority
    # on server.json, so it catches anything the hand-written checks above do not know
    # about. It needs no credentials and publishes nothing.
    step("Validating server.json against the registry")
    run([str(PUBLISHER_EXE), "validate"])
    ok("server.json is valid")


def verify_registry_auth():
    # Authenticate before anything is transmitted. The device flow is interactive and
    # times out if nobody is at the keyboard, which is easy to miss when the release is
    # the last step of a long unattended deploy. Failing here costs nothing; failing
    # after the PyPI upload cannot be undone, because PyPI versions are immutable.
    #
    # An existing credential file means a previous login is still on disk. It is taken
    # at face value: if it has expired the publish fails and the fix is to log in again,
    # which is a better trade than prompting on every run.
    step("Authenticating with the MCP Registry")
    if any(REPO.glob(".mcpregistry_*")):
        ok("existing registry credentials found")
        return

    print("    This is an interactive GitHub device flow. A code appears below:")
    print("    open https://github.com/login/device and enter it before it expires.")
    run([str(PUBLISHER_EXE), "login", "github"])
    ok("authenticated")


def preflight():
    # Reached only once a channel is known to be missing this version, so the test run
    # and the interactive login below are paid for by a run that is going to publish.
    # Ordered cheapest first, so an obvious mistake fails in milliseconds rather than
    # after a two-minute test run.
    verify_working_tree()
    verify_tests()
    verify_publisher_present()
    verify_server_json()
    verify_registry_auth()


# ============================================================================
# BUILD AND PUBLISH
# ============================================================================

def build(version):
    # dist/ is emptied first so a stale artifact from an earlier version can never be
    # uploaded by a glob. This is what makes the build idempotent.
    step("Building")
    dist = REPO / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    run(["uv", "build"])

    expected = [
        dist / f"rationalbloks_mcp-{version}-py3-none-any.whl",
        dist / f"rationalbloks_mcp-{version}.tar.gz",
    ]
    missing = [path.name for path in expected if not path.exists()]
    if missing:
        raise RuntimeError(f"build did not produce: {', '.join(missing)}")
    ok(f"built {expected[0].name} and {expected[1].name}")


def read_pypi_token():
    # The token file is an operator notes file, not a bare token: it carries headings,
    # rule lines and a reminder command, with the token on its own line among them. So
    # the token is extracted rather than assumed to be the entire file.
    #
    # Exactly one distinct token must be present. None means the file is not what it
    # claims. More than one means the file cannot say which is current, and guessing at
    # a credential is not a thing this script does.
    #
    # utf-8-sig, not utf-8: a byte order mark is not whitespace, so .strip() leaves it
    # attached and the token silently stops matching.
    if not PYPI_TOKEN_FILE.exists():
        raise RuntimeError(f"PyPI token not found at {PYPI_TOKEN_FILE}")

    text = PYPI_TOKEN_FILE.read_text(encoding="utf-8-sig", errors="replace")
    found = set(re.findall(r"pypi-[A-Za-z0-9_\-]+", text))

    if not found:
        raise RuntimeError(
            f"no pypi- token found in {PYPI_TOKEN_FILE.name}; the file should contain "
            f"the token somewhere in its text"
        )
    if len(found) > 1:
        raise RuntimeError(
            f"{PYPI_TOKEN_FILE.name} holds {len(found)} different pypi- tokens; leave "
            f"exactly one so there is no question which is current"
        )
    return found.pop()


def publish_pypi(version):
    step("Publishing to PyPI")
    token = read_pypi_token()
    run(["uv", "publish", "--token", token], secret=token)
    ok(f"{PACKAGE_NAME} {version} uploaded")


def publish_registry(version):
    # Authentication and server.json validation both happened in preflight. This step
    # runs after the PyPI upload because the registry validates that the package
    # version it is given already exists on PyPI.
    step("Publishing to the MCP Registry")
    run([str(PUBLISHER_EXE), "publish"])
    ok(f"{SERVER_NAME} {version} submitted")


# ============================================================================
# VERIFICATION
# ============================================================================
# Neither index serves a new version instantly, so each publish is confirmed before the
# next step runs. This is not politeness: the registry validates the version against
# PyPI, so publishing to it before PyPI has indexed the upload is a race that fails on
# a release that actually succeeded.

def read_pypi_version():
    return get_json(PYPI_JSON_URL)["info"]["version"]


def read_registry_version():
    # None means the registry holds no entry for this server at all, which is the normal
    # state before a first publish rather than a failure. Every caller compares against
    # the version it wants, so absence and staleness take the same path: publish, then
    # wait for it to appear.
    for entry in get_json(REGISTRY_SEARCH_URL).get("servers", []):
        server = entry.get("server", entry)
        if server.get("name") == SERVER_NAME:
            return server.get("version")
    return None


def wait_for(label, reader, version):
    for attempt in range(1, VERIFY_ATTEMPTS + 1):
        current = reader()
        if current == version:
            ok(f"{label} serves {version}")
            return
        print(f"    ... {label} serves {current or 'no entry'} ({attempt}/{VERIFY_ATTEMPTS})")
        time.sleep(VERIFY_INTERVAL)
    raise RuntimeError(f"{label} did not serve {version} within the wait window")


# ============================================================================
# STATUS
# ============================================================================

def print_channel_status():
    # The read-only view of the same two channels this script publishes to. It lives
    # here rather than in deploy_all.py so the drift check and the release agree on
    # what each channel serves by construction, rather than by two implementations
    # happening to stay in step. Reads only: it never authenticates or publishes.
    local = read_pyproject_version()
    channels = [
        ("PyPI",         PACKAGE_NAME,  read_pypi_version()),
        ("MCP Registry", "server.json", read_registry_version()),
    ]

    print(f"\n  {'channel':<14} {'artifact':<20} {'published':<13} {'local':<13} state")
    print(f"  {'-' * 14} {'-' * 20} {'-' * 13} {'-' * 13} {'-' * 9}")

    behind = 0
    for channel, artifact, published in channels:
        state = "IN SYNC" if published == local else "STALE"
        if state != "IN SYNC":
            behind += 1
        print(f"  {channel:<14} {artifact:<20} {published or 'absent':<13} {local:<13} {state}")

    print("")
    if behind:
        print(f"  {behind} channel(s) behind - run: python deploy_all.py all")
    else:
        ok(f"PyPI and the MCP Registry both serve {local}")


# ============================================================================
# MAIN
# ============================================================================
# One try/except at the top level: every step above raises, and any failure must stop
# the release rather than be handled and carried forward.

try:
    bar = "=" * 76

    mode = sys.argv[1] if len(sys.argv) > 1 else "release"
    if mode not in ("release", "status"):
        raise RuntimeError(f"unknown mode {mode!r}; valid modes are: release, status")

    if mode == "status":
        print_channel_status()
        sys.exit(0)

    print(f"\n{bar}\n  RATIONALBLOKS MCP - RELEASE\n{bar}")

    # What is missing is decided before anything is verified, built or transmitted, so a
    # run with nothing to publish never reaches the test suite or the interactive login.
    release_version = verify_manifests()
    on_pypi, on_registry = read_channel_state(release_version)

    if on_pypi and on_registry:
        print(f"\n{bar}")
        print(f"  NOTHING TO RELEASE - both channels already serve {release_version}")
        print(f"{bar}\n")
        sys.exit(0)

    preflight()

    # PyPI first, and its index must actually serve the version before the registry is
    # told about it: the registry validates the package version against PyPI, so this
    # ordering is a requirement rather than a preference.
    if not on_pypi:
        build(release_version)
        publish_pypi(release_version)
        wait_for("PyPI", read_pypi_version, release_version)

    if not on_registry:
        publish_registry(release_version)
        wait_for("MCP Registry", read_registry_version, release_version)

    print(f"\n{bar}")
    print(f"  RELEASED {release_version} - PyPI and MCP Registry both serve it")
    print(f"  The hosted server is separate: python deploy_all.py vps3")
    print(f"{bar}\n")

except Exception as error:
    bar = "=" * 76
    print(f"\n{bar}")
    print(f"  RELEASE FAILED")
    print(f"{bar}")
    print(f"  {type(error).__name__}: {error}")
    print(f"\n  Chain of events halted. Nothing further was published.\n")
    sys.exit(1)
