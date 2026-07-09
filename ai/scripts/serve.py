#!/usr/bin/env python3
"""Serve the AI-assisted research workbench dashboard locally.

Routing model
-------------
The browser URL is the file's path relative to the repository root, e.g.
``/simulations/scratch/2026-06-28-foo/README.md``. That makes deep links and
page reloads work, and lets Markdown-relative image links (``figures/x.png``)
resolve against the real directory of the file being viewed.

For any GET the server returns one of three things:

* the dashboard **shell** (``dashboard/index.html``) -- for ``/``, directories,
  and any *viewable* text/source file (``.md``, ``.py`` ...). The shell's
  client script then reads ``location.pathname`` and fetches the raw content.
* the **raw bytes** of a file -- for ``?raw=1`` requests (used by the client to
  fetch Markdown/source), for non-viewable assets (images, ``.npz`` ...), and
  for the dashboard's own static assets under ``/dashboard/``.
* a small **JSON file tree** -- for ``/__tree__?path=<dir>&depth=<n>``, consumed
  by the sidebar.
"""

from __future__ import annotations

import argparse
import http.server
import json
import mimetypes
import socketserver
from functools import partial
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

# Text/source files rendered as a page (shell served; client renders content).
VIEWABLE_EXT = {
    ".md", ".markdown", ".txt", ".py", ".js", ".sh", ".ps1", ".yaml", ".yml",
    ".toml", ".json", ".bib", ".cfg", ".ini", ".csv", ".tex", ".html", ".htm",
}

# Extensions worth listing in the sidebar file tree.
TREE_EXT = {
    ".md", ".markdown", ".txt", ".py", ".js", ".sh", ".ps1", ".yaml", ".yml",
    ".toml", ".json", ".bib", ".cfg", ".ini", ".csv", ".tex",
}

# Directories never crawled or listed.
SKIPPED_DIRS = {
    ".git", ".agents", ".codex", "__pycache__", "node_modules", ".venv",
    ".mypy_cache", ".pytest_cache", "pdfs",
}


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    # ``self.directory`` (the repo root) is injected via functools.partial.

    @property
    def root(self) -> Path:
        return Path(self.directory).resolve()

    # ----------------------------------------------------------------- routing
    def do_GET(self) -> None:
        status, content_type, body, extra = self._route()
        self._send(status, content_type, body, extra, with_body=True)

    def do_HEAD(self) -> None:
        status, content_type, body, extra = self._route()
        self._send(status, content_type, body, extra, with_body=False)

    def _send(self, status, content_type, body, extra, with_body) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # Local dev dashboard: never cache, so auto-refresh always sees edits.
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if with_body:
            self.wfile.write(body)

    def _route(self):
        parts = urlsplit(self.path)
        raw_path = unquote(parts.path)
        query = parse_qs(parts.query)

        # 1. File-tree endpoint for the sidebar.
        if raw_path == "/__tree__":
            return self._tree_response(query)

        rel = raw_path.lstrip("/")

        # 2. Dashboard's own static assets and shell.
        if rel == "" or rel == "dashboard" or rel == "dashboard/":
            return self._shell_response()
        if rel.startswith("dashboard/"):
            target = self._safe_target(rel)
            if target is None or not target.is_file():
                return self._not_found(rel)
            if target.name == "index.html":
                return self._shell_response()
            return self._raw_response(target)

        # 3. Everything else maps to a repository file or directory.
        target = self._safe_target(rel)
        if target is None:
            return self._forbidden(rel)
        if target.is_dir():
            return self._shell_response()
        if not target.is_file():
            return self._not_found(rel)

        want_raw = query.get("raw", ["0"])[0] not in ("0", "", "false")
        if want_raw:
            return self._raw_response(target)
        if target.suffix.lower() in VIEWABLE_EXT:
            return self._shell_response()
        return self._raw_response(target)

    # --------------------------------------------------------------- responses
    def _shell_response(self):
        shell = self.root / "dashboard" / "index.html"
        try:
            body = shell.read_bytes()
        except OSError:
            return self._not_found("dashboard/index.html")
        return 200, "text/html; charset=utf-8", body, None

    def _raw_response(self, target: Path):
        try:
            body = target.read_bytes()
        except OSError:
            return self._not_found(str(target))
        ctype, _ = mimetypes.guess_type(target.name)
        if ctype is None:
            ctype = "text/plain"
        if ctype.startswith("text/") and "charset" not in ctype:
            ctype += "; charset=utf-8"
        return 200, ctype, body, None

    def _tree_response(self, query):
        rel = query.get("path", [""])[0].strip().strip("/")
        try:
            depth = int(query.get("depth", ["4"])[0])
        except ValueError:
            depth = 4
        base = self._safe_target(rel) if rel else self.root
        if base is None or not base.is_dir():
            nodes = []
        else:
            nodes = self._build_tree(base, rel, depth)
        body = json.dumps(nodes).encode("utf-8")
        return 200, "application/json; charset=utf-8", body, None

    def _build_tree(self, directory: Path, rel: str, depth: int):
        dirs, files = [], []
        try:
            entries = sorted(directory.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            return []
        for entry in entries:
            name = entry.name
            if name.startswith(".") or name in SKIPPED_DIRS:
                continue
            child_rel = f"{rel}/{name}" if rel else name
            if entry.is_dir():
                children = self._build_tree(entry, child_rel, depth - 1) if depth > 0 else []
                if children:
                    dirs.append({
                        "type": "directory",
                        "label": name,
                        "path": child_rel,
                        "children": children,
                    })
            elif entry.is_file() and entry.suffix.lower() in TREE_EXT:
                files.append({"type": "file", "label": name, "path": child_rel})

        def sort_key(node):
            is_index = node["path"].endswith("/index.md") or node["path"] == "index.md"
            return (0 if is_index else 1, node["label"].lower())

        dirs.sort(key=sort_key)
        files.sort(key=sort_key)
        return dirs + files

    # ------------------------------------------------------------------ errors
    def _not_found(self, rel):
        body = f"Not found: {rel}".encode("utf-8")
        return 404, "text/plain; charset=utf-8", body, None

    def _forbidden(self, rel):
        body = f"Forbidden: {rel}".encode("utf-8")
        return 403, "text/plain; charset=utf-8", body, None

    # ------------------------------------------------------------------- safety
    def _safe_target(self, rel: str):
        """Resolve ``rel`` under the repo root, refusing escapes via ``..``."""
        if not rel:
            return self.root
        target = (self.root / rel).resolve()
        if target == self.root or target.is_relative_to(self.root):
            return target
        return None

    def log_message(self, fmt, *args):  # quieter console
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the local research dashboard.")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on (default: 8000).")
    parser.add_argument("--host", default="127.0.0.1", help="Host/interface to bind (default: 127.0.0.1).")
    parser.add_argument(
        "--root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
        help="Repository root to serve (default: parent of this script directory).",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    mimetypes.add_type("text/markdown", ".md")
    handler = partial(DashboardHandler, directory=str(root))

    with ReusableTCPServer((args.host, args.port), handler) as httpd:
        url = f"http://{args.host}:{args.port}/"
        print(f"Serving {root}")
        print(f"Open {url}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
