"""Vercel serverless entrypoint for the OpenGlossa MCP server.

Exposes the FastMCP Streamable HTTP app (stateless mode) as the module-level
``app`` ASGI callable, which Vercel's Python runtime serves automatically.
``vercel.json`` rewrites the canonical ``/mcp`` path to this function.

Stateless mode is mandatory on serverless: each request is an isolated, fresh
invocation, so no MCP session state can be preserved between calls.

Data: the server is seeded with the bundled, fully-cited demo TM
(``public/downloads/openglossa_demo.jsonl``, 200 official Fedlex segments), so
``search_parallel`` / ``verify_translation`` work without any network. The live
tools (``get_official_text``, TERMDAT-backed ``lookup_term``) fetch official
sources on demand and degrade gracefully if upstream is slow or unavailable.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from openglossa.mcp.server import Repository, build_server  # noqa: E402
from openglossa.schemas import TranslationUnit  # noqa: E402

# Prefer the copy bundled next to the function (guaranteed in the lambda),
# fall back to the public/ static asset for local runs.
_DEMO_CANDIDATES = [
    Path(__file__).resolve().parent / "tm.jsonl",
    ROOT / "public" / "downloads" / "openglossa_demo.jsonl",
]


def _load_repo() -> Repository:
    repo = Repository()
    for path in _DEMO_CANDIDATES:
        if path.exists():
            repo.tus = [
                TranslationUnit.model_validate_json(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            break
    return repo


# Semantic search (LaBSE/torch) is intentionally disabled here: it exceeds the
# serverless bundle/memory budget. search_parallel falls back to the lexical
# baseline, which is deterministic and fully cited.
_server = build_server(
    _load_repo(),
    termdat_live=True,
    index=None,
    index_path=None,
    stateless=True,
)

# The MCP Streamable HTTP app serves the protocol at /mcp.
_mcp_app = _server.streamable_http_app()

# Static assets (styles.css, app.js, data/, downloads/) are served by Vercel's
# edge from public/. The function only needs the homepage HTML for the SPA-style
# fallback ("/" and any non-asset route), bundled next to the function.
_INDEX_HTML = (Path(__file__).resolve().parent / "_index.html").read_bytes()


async def _send_index(send) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/html; charset=utf-8")],
        }
    )
    await send({"type": "http.response.body", "body": _INDEX_HTML})


async def app(scope, receive, send):
    """ASGI dispatcher: /mcp* -> MCP server, everything else -> homepage.

    The lifespan event is delegated to the MCP app so its Streamable HTTP
    session manager is started/stopped correctly on the serverless host.
    """
    if scope["type"] == "lifespan":
        await _mcp_app(scope, receive, send)
        return
    path = scope.get("path", "/")
    if path == "/mcp" or path.startswith("/mcp/"):
        await _mcp_app(scope, receive, send)
        return
    await _send_index(send)
