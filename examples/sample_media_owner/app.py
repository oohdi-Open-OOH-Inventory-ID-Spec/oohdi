import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

MEDIA_OWNER_DOMAIN = "example-media-owner.oohdi.org"
NAMESPACE = "org.oohdi.example-media-owner"

owner_meta = {
    "id": f"{NAMESPACE}/oohdi",
    "organization": "Example Media Owner",
    "street_address": "42 Lantern Avenue",
    "city": "Portland",
    "region": "OR",
    "country": "US",
    "phone_number": "+1-503-555-0148",
    "email_address": "hello@example-media-owner.oohdi.org",
    "website": "https://example-media-owner.oohdi.org",
    "created_at": "2025-01-10T09:00:00Z",
    "updated_at": "2025-06-15T09:00:00Z",
}

records = {
    "org.oohdi.example-media-owner/oohdi/emp-001": {
        "identity": {"id": "org.oohdi.example-media-owner/oohdi/emp-001", "name": "Harborview Digital 01", "description": "Digital display facing Harbor Avenue"},
        "state": {"type": "digital", "status": "active"},
        "inventory": {"unit_type": "display"},
        "location": {"location_type": "fixed", "point": {"latitude": 45.5231, "longitude": -122.6765}, "bounds": None},
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-06-15T10:00:00Z",
    }
}


class SampleMediaOwnerHandler(BaseHTTPRequestHandler):
    server_version = "OOHDI Sample Media Owner/0.1"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.strip("/")
        segments = [s for s in path.split("/") if s]

        if path in {"", "/"}:
            self._send_html(
                200,
                f"""
                <!doctype html>
                <html lang=\"en\">
                <head>
                  <meta charset=\"utf-8\" />
                  <title>Example Media Owner</title>
                  <style>
                    body {{ font-family: Arial, sans-serif; margin: 2rem; background: #f5f8ff; color: #12233a; }}
                    .card {{ max-width: 760px; margin: 0 auto; background: white; border-radius: 14px; padding: 2rem; box-shadow: 0 10px 25px rgba(18,35,58,0.08); }}
                    h1 {{ color: #0d2d54; }}
                    code {{ background: #edf5ff; padding: 0.2rem 0.5rem; border-radius: 6px; }}
                  </style>
                </head>
                <body>
                  <div class=\"card\">
                    <h1>Example Media Owner</h1>
                    <p>This is a fictional OOHDI media owner landing page for <strong>{MEDIA_OWNER_DOMAIN}</strong>.</p>
                    <p>Namespace: <code>{NAMESPACE}</code></p>
                    <p>Registry discovery record: <code>_oohdi.{MEDIA_OWNER_DOMAIN} TXT "v=OOHDI1; r=example-registry.oohdi.org;"</code></p>
                    <p>Example inventory lookup: <code>https://example-registry.oohdi.org/oohdi/{NAMESPACE}</code></p>
                  </div>
                </body>
                </html>
                """,
            )
            return

        if path == "health":
            self._send_json(200, {"status": "ok"})
            return

        if len(segments) >= 2 and segments[0] == "oohdi":
            namespace = segments[1]
            if namespace != NAMESPACE:
                self._send_json(
                    421,
                    {
                        "error_code": "not_authoritative",
                        "message": "This media owner service is not authoritative for the requested media owner namespace.",
                        "authoritative_namespace": NAMESPACE,
                    },
                )
                return

            if len(segments) == 2:
                self._send_json(200, owner_meta)
                return

            if len(segments) == 3:
                identity_id = f"{namespace}/oohdi/{segments[2]}"
                if identity_id in records:
                    self._send_json(200, records[identity_id])
                    return
                self._send_json(404, {"error_code": "not_found", "message": "Inventory record not found."})
                return

        self._send_json(404, {"error_code": "not_found", "message": "Resource not found."})

    def _send_json(self, status_code, payload):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status_code, html):
        body = html.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    host = os.environ.get("OOHDI_HOST", "0.0.0.0")
    port = int(os.environ.get("OOHDI_PORT", "8080"))
    server = HTTPServer((host, port), SampleMediaOwnerHandler)
    print(f"Sample media owner listening on http://{host}:{port}")
    server.serve_forever()
