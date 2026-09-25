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
            self._send_json(200, {
                "service": "OOHDI sample media owner",
                "media_owner": MEDIA_OWNER_DOMAIN,
                "namespace": NAMESPACE,
                "status": "sample",
            })
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

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    host = os.environ.get("OOHDI_HOST", "0.0.0.0")
    port = int(os.environ.get("OOHDI_PORT", "8080"))
    server = HTTPServer((host, port), SampleMediaOwnerHandler)
    print(f"Sample media owner listening on http://{host}:{port}")
    server.serve_forever()
