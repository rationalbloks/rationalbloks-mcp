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
# is nothing to release and the run ends there, without running the tests or touching
# the network again. That is what lets this sit at the FRONT of `deploy_all.py all`
# and cost two HTTP reads on every deploy that has nothing to publish.
#
# FULLY UNATTENDED:
# Both channels authenticate from stored secrets, so a release never waits for a human.
# See REGISTRY IDENTITY below for why the registry half is domain-backed.
#
# USAGE:
#   python release.py           # publish whatever the two channels are missing
#   python release.py status    # read-only: what each channel serves, no side effects
# ============================================================================

import base64
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.error
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


# ============================================================================
# REGISTRY IDENTITY
# ============================================================================
# The server is published under the reverse-DNS form of a domain this company owns.
# That is what every established publisher does - com.stripe/mcp, com.notion/mcp,
# com.atlassian/atlassian-mcp-server - while io.github.* namespaces belong to
# individual developers.
#
# It is also the only form that works here. The registry grants an io.github.<org>
# namespace from GitHub identity, and since registry v1.8.0 grants it only to org
# Owners. It is currently not granting it at all: four issues report a token minted
# with the personal namespace only, despite Owner role and public membership
# (modelcontextprotocol/registry 1468, 1527, 1537, 1551, all open). The old
# io.github.rationalbloks name is unreachable until that is fixed.
#
# Domain ownership is proved by signing a challenge with a key whose public half is
# published as a TXT record on the domain. No device code, no browser, nothing that
# expires while an unattended deploy is running.

SERVER_NAME = "com.rationalbloks/mcp"

DNS_DOMAIN = "rationalbloks.com"
DNS_KEY_FILE = Path(
    r"C:\Users\velos\OneDrive\RATIONALBLOKS\01_RELATIONAL_DATABLOK\00_CYBER_CRITICAL"
    r"\MCP_REGISTRY_DNS_KEY.pem"
)

# The public half of that key, exactly as it must appear in DNS. It is public by
# nature, so it is committed: verify_dns_proof() compares the live TXT record against
# it, and rotating the key means changing this line and the DNS record together.
DNS_PUBLIC_KEY = "8rHaodJWY3LAtptPtS9obIK5OnlfptnQXzNLAi2t700="
DNS_TXT_VALUE = f"v=MCPv1; k=ed25519; p={DNS_PUBLIC_KEY}"

# Resolved over DNS-over-HTTPS so the check does not depend on whatever resolver the
# operator's machine happens to be using.
DNS_QUERY_URL = f"https://cloudflare-dns.com/dns-query?name={DNS_DOMAIN}&type=TXT"

PYPI_JSON_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
# version=latest is load-bearing. Without it the search returns EVERY version a server
# has ever published, oldest first, so reading the first match reports a version that is
# permanently stale. That failed a release which had in fact succeeded: 0.12.2 was live
# on the registry and the verification below read 0.12.1 twenty times, then halted the
# whole deploy queued behind it. With it the registry returns one entry per server.
REGISTRY_SEARCH_URL = (
    "https://registry.modelcontextprotocol.io/v0.1/servers"
    "?search=rationalbloks&version=latest"
)
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

# PyPI and the registry are third-party services that go briefly unavailable: a read
# timeout and an HTTP 500 from the registry have both interrupted a release here. A
# transport fault is not the release failing, so it is retried with backoff, the same
# rule deploy_all.py already applies to an SSH connection error. When the attempts are
# spent it raises and the chain halts.
#
# The timeout is generous because the registry earns it. Measured back to back, the
# same search returned in 0.8s, 22.8s and 32.6s, while PyPI answered every call in
# under half a second. A 30s timeout sat inside that spread, so the registry being
# ordinarily slow read as a transport fault and failed a release. 60s clears every
# response measured, and a service that is genuinely down still fails on connect.
NETWORK_ATTEMPTS = 4
NETWORK_BACKOFF = 5
NETWORK_TIMEOUT = 60


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


def get_json(url, headers=None):
    # The one way this script reads JSON over HTTP, so every index read gets the same
    # retry rule. A malformed body still raises on the first attempt: only transport
    # faults are transient. A release must never continue on a guess about what an
    # index holds, so exhausting the attempts halts the chain.
    request = urllib.request.Request(url, headers=headers or {})
    for attempt in range(1, NETWORK_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=NETWORK_TIMEOUT) as response:
                return json.loads(response.read().decode("utf-8"))
        except OSError as error:
            # A 4xx is the service's considered answer, not a blip, so it is never
            # retried. Everything else here is a transport fault or a 5xx.
            settled = isinstance(error, urllib.error.HTTPError) and error.code < 500
            if settled or attempt == NETWORK_ATTEMPTS:
                raise
            wait = NETWORK_BACKOFF * attempt
            print(f"    ... {type(error).__name__} from {url}; "
                  f"retry {attempt}/{NETWORK_ATTEMPTS - 1} in {wait}s")
            time.sleep(wait)


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


def verify_dns_proof():
    # The registry proves domain ownership by reading this TXT record and checking a
    # signature against it. Verifying it here turns a missing or stale record into a
    # failure that costs milliseconds and prints the exact fix, rather than one that
    # surfaces after the PyPI upload, which cannot be taken back.
    step("Verifying the DNS ownership record")
    if not DNS_KEY_FILE.exists():
        raise RuntimeError(f"registry signing key not found at {DNS_KEY_FILE}")

    answers = get_json(DNS_QUERY_URL,
                       headers={"accept": "application/dns-json"}).get("Answer", [])

    published = [answer.get("data", "").strip('"') for answer in answers]
    if DNS_TXT_VALUE not in published:
        raise RuntimeError(
            f"{DNS_DOMAIN} does not publish the registry ownership record.\n"
            f"  Add this TXT record, let it propagate, then re-run:\n"
            f"    name : {DNS_DOMAIN}\n"
            f"    type : TXT\n"
            f"    value: {DNS_TXT_VALUE}"
        )
    ok(f"{DNS_DOMAIN} publishes the expected ownership record")


def preflight():
    # Reached only once a channel is known to be missing this version, so the test run
    # below is paid for by a run that is going to publish. Ordered cheapest first, so an
    # obvious mistake fails in milliseconds rather than after a two-minute test run.
    # Nothing here is interactive: the DNS record is proved, not logged into.
    verify_working_tree()
    verify_tests()
    verify_publisher_present()
    verify_server_json()
    verify_dns_proof()


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


def read_dns_private_key():
    # An Ed25519 PKCS#8 key is 48 DER bytes: a 16-byte header then the 32-byte seed,
    # which is exactly what the publisher wants as hex. Decoding it here rather than
    # shelling out to openssl drops a runtime dependency and keeps the key out of any
    # subprocess error text.
    body = "".join(
        line for line in DNS_KEY_FILE.read_text(encoding="utf-8").splitlines()
        if not line.startswith("-----")
    )
    der = base64.b64decode(body)
    if len(der) != 48:
        raise RuntimeError(
            f"{DNS_KEY_FILE.name} is {len(der)} DER bytes; an Ed25519 PKCS#8 key is 48"
        )
    return der[-32:].hex()


def publish_registry(version):
    # Authentication runs HERE rather than in preflight because the registry issues a
    # token that lives 300 seconds, and the PyPI index wait above can consume all of
    # it. Authenticating last is free precisely because it is non-interactive: the DNS
    # record was already proved correct in preflight, so this cannot stall on a human.
    #
    # The publish itself runs after the PyPI upload because the registry validates that
    # the package version it is given already exists on PyPI.
    step("Authenticating with the MCP Registry")
    private_key = read_dns_private_key()
    run([str(PUBLISHER_EXE), "login", "dns",
         "--domain", DNS_DOMAIN, "--private-key", private_key], secret=private_key)
    ok(f"authenticated as {DNS_DOMAIN}")

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
    # The search also matches the retired io.github entry, so the name filter is what
    # picks this server out, and version=latest is what makes the single entry it
    # returns the current one. None means the registry holds no entry for this server
    # at all, which is the normal state before a first publish rather than a failure.
    # Every caller compares against the version it wants, so absence and staleness take
    # the same path: publish, then wait for it to appear.
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
    print("  The hosted server is separate: python deploy_all.py vps3")
    print(f"{bar}\n")

except Exception as error:
    bar = "=" * 76
    print(f"\n{bar}")
    print("  RELEASE FAILED")
    print(f"{bar}")
    print(f"  {type(error).__name__}: {error}")
    print("\n  Chain of events halted. Nothing further was published.\n")
    sys.exit(1)
