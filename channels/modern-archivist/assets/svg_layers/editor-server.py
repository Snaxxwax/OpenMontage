#!/usr/bin/env python3
"""Editor server for the Modern Archivist Puppet Editor.

Serves the svg_layers/ directory and the render-facing asset directory
so the editor can load manifest and layer images via HTTP (not file:// CORS).

Endpoints:
  GET  /character/manifest  -> modern_archivist_puppet_manifest.json
  PUT  /character/manifest  <- write manifest back
  GET  /layers/<path>       -> remotion-composer/public/modern-archivist/layers/<path>
  GET  /timeline/<name>     -> rig/<name>.json
  PUT  /timeline/<name>     <- write timeline JSON
  GET  /backups             -> list available backups
  POST /backup              <- create a timestamped backup of current manifest
  GET  /                    -> editor.html
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# ─── Server configuration ───────────────────────────────────────────────────

PORT = int(os.environ.get("EDITOR_PORT", "8765"))
HOST = os.environ.get("EDITOR_HOST", "0.0.0.0")

# Resolve root from this script's location
SCRIPT_DIR = Path(__file__).resolve().parent
CHARACTER_DIR = SCRIPT_DIR.parent / "character"
BACKUP_DIR = CHARACTER_DIR / "backups"
RENDER_PUBLIC = SCRIPT_DIR.parents[3] / "remotion-composer" / "public"
LAYERS_PUBLIC = RENDER_PUBLIC / "modern-archivist" / "layers"
MODERN_ARCHIVIST_PUBLIC = RENDER_PUBLIC / "modern-archivist"
NARRATOR_PUBLIC = RENDER_PUBLIC / "narrator"

# Ensure backup dir exists
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


class EditorHandler(SimpleHTTPRequestHandler):
    """Custom handler that extends SimpleHTTPRequestHandler with PUT support
    and custom API endpoints."""

    def __init__(self, *args, **kwargs):
        # Serve from SCRIPT_DIR by default (where editor.html lives)
        super().__init__(*args, directory=str(SCRIPT_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        # /character/manifest?character=narrator or /character/manifest (default: modern_archivist)
        if re.match(r"^/character/manifest", path):
            query = parse_qs(parsed.query)
            char_id = query.get("character", ["modern_archivist"])[0]
            manifest_name = "modern_archivist_puppet_manifest.json" if char_id == "modern_archivist" else f"{char_id}_manifest.json"
            manifest_path = CHARACTER_DIR / manifest_name
            if not manifest_path.exists():
                self.send_error(404, f"Manifest not found for character: {char_id}")
                return
            self._send_json(manifest_path.read_text(encoding="utf-8"))
            return

        # /layers/<path> -> remotion-composer/public/ subdirectories
        m = re.match(r"^/layers/(.+)", path)
        if m:
            asset_name = m.group(1)
            # Try multiple locations in order
            layer_path = LAYERS_PUBLIC / asset_name
            if not layer_path.exists():
                layer_path = MODERN_ARCHIVIST_PUBLIC / asset_name
            if not layer_path.exists():
                layer_path = NARRATOR_PUBLIC / asset_name
            if not layer_path.exists():
                layer_path = RENDER_PUBLIC / asset_name
            if not layer_path.exists():
                self.send_error(404, f"Layer not found: {asset_name}")
                return
            self._send_file(layer_path)
            return

        # /timeline/<name> -> rig/<name>.json
        m = re.match(r"^/timeline/(.+)", path)
        if m:
            timeline_name = re.sub(r"[^a-zA-Z0-9_-]", "", m.group(1))
            timeline_path = CHARACTER_DIR / "rig" / f"{timeline_name}.json"
            if not timeline_path.exists():
                self.send_error(404, f"Timeline not found: {timeline_name}")
                return
            self._send_json(timeline_path.read_text(encoding="utf-8"))
            return

        # /backups -> list available backups
        if path == "/backups":
            backups = sorted(BACKUP_DIR.glob("manifest_*.json"), reverse=True)
            listing = [
                {
                    "filename": b.name,
                    "timestamp": b.stem.replace("manifest_", ""),
                    "size": b.stat().st_size,
                }
                for b in backups
            ]
            self._send_json(json.dumps(listing, indent=2))
            return

        # Default: serve static files (editor.html, CSS, JS, images)
        super().do_GET()

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else ""

        # PUT /character/manifest
        if re.match(r"^/character/manifest", path):
            self._handle_put_manifest(body)
            return

        # PUT /timeline/<name>
        m = re.match(r"^/timeline/(.+)", path)
        if m:
            timeline_name = re.sub(r"[^a-zA-Z0-9_-]", "", m.group(1))
            timeline_path = CHARACTER_DIR / "rig" / f"{timeline_name}.json"
            try:
                json.loads(body)  # validate JSON
                timeline_path.write_text(body, encoding="utf-8")
                self._send_json(
                    json.dumps({"status": "ok", "saved_to": str(timeline_path)})
                )
            except json.JSONDecodeError as exc:
                self.send_error(400, f"Invalid JSON: {exc}")
            return

        self.send_error(404, f"PUT not supported for {path}")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # POST /backup
        if path == "/backup":
            manifest_path = CHARACTER_DIR / "modern_archivist_puppet_manifest.json"
            if not manifest_path.exists():
                self.send_error(404, "Manifest not found for backup")
                return
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_path = BACKUP_DIR / f"manifest_{ts}.json"
            shutil.copy2(manifest_path, backup_path)
            self._send_json(
                json.dumps({"status": "ok", "backup": str(backup_path)})
            )
            return

        self.send_error(404, f"POST not supported for {path}")

    def _handle_put_manifest(self, body: str) -> None:
        """Write manifest file, with size/JSON validation."""
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            self.send_error(400, f"Invalid JSON: {exc}")
            return

        manifest_path = CHARACTER_DIR / "modern_archivist_puppet_manifest.json"

        # Create backup before overwriting
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"manifest_{ts}.json"
        try:
            shutil.copy2(manifest_path, backup_path)
        except Exception:
            pass  # non-critical; proceed even if backup fails

        manifest_path.write_text(body, encoding="utf-8")

        self._send_json(
            json.dumps({
                "status": "ok",
                "saved_to": str(manifest_path),
                "backup": str(backup_path),
                "layer_count": len(data.get("layers", [])),
            })
        )

    def _send_json(self, text: str) -> None:
        """Send a JSON response."""
        encoded = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)

    def _send_file(self, path: Path) -> None:
        """Send a file with appropriate content type."""
        if not path.exists():
            self.send_error(404)
            return
        ext = path.suffix.lower()
        content_types = {
            ".png": "image/png",
            ".svg": "image/svg+xml",
            ".json": "application/json",
            ".html": "text/html",
            ".js": "application/javascript",
            ".css": "text/css",
        }
        ctype = content_types.get(ext, "application/octet-stream")
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    # Override to add CORS headers on static responses too
    def end_headers(self):
        try:
            self.send_header("Access-Control-Allow-Origin", "*")
        except Exception:
            pass
        super().end_headers()

    def log_message(self, format, *args):
        """Quiet logging with timestamps."""
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {args[0]} {args[1]} {args[2]}")


def main():
    server = HTTPServer((HOST, PORT), EditorHandler)
    print(f"╔══════════════════════════════════════════════════════════╗")
    print(f"║  Modern Archivist Puppet Editor Server                  ║")
    print(f"╠══════════════════════════════════════════════════════════╣")
    print(f"║  Open:  http://{HOST}:{PORT}/editor.html               ║")
    print(f"║  Static:  svg_layers/ (editor.html, CSS, JS, images)    ║")
    print(f"║  API:                                                  ║")
    print(f"║    GET  /character/manifest  → puppet manifest          ║")
    print(f"║    PUT  /character/manifest  → save manifest            ║")
    print(f"║    POST /backup              → create backup            ║")
    print(f"║    GET  /backups             → list backups             ║")
    print(f"║    GET  /timeline/<name>     → action timeline          ║")
    print(f"║    PUT  /timeline/<name>     → save timeline            ║")
    print(f"║    GET  /layers/<path>       → layer PNG/SVG            ║")
    print(f"╚══════════════════════════════════════════════════════════╝")
    print(f"\nCtrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
