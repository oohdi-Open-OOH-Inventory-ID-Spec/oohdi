import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict
from urllib.parse import urlparse


EXAMPLE_RECORD = {
    "identity": {
        "id": "com.foobaroutdoor/oohdi/abc-1234",
        "name": "Times Square Digital – Upper Panel",
        "description": "Upper sellable segment of Times Square Digital"
    },
    "state": {
        "type": "digital",
        "status": "active"
    },
    "inventory": {
        "unit_type": "segment",
        "parent_unit_id": "com.foobaroutdoor/oohdi/tsq-panel-01"
    },
    "location": {
        "location_type": "fixed",
        "point": {
            "latitude": 40.712776,
            "longitude": -74.005974
        },
        "bounds": None
    },
    "capabilities": {
        "media_formats": [
            {
                "type": "digital_image",
                "enabled": True,
                "min_duration_seconds": 8,
                "max_duration_seconds": 8
            },
            {
                "type": "digital_video",
                "enabled": True,
                "min_duration_seconds": 8,
                "max_duration_seconds": 30
            }
        ]
    },
    "taxonomy": {
        "venue_type_id": "openooh:venue:301"
    },
    "extensions": {},
    "created_at": "2025-01-01T12:00:00Z",
    "updated_at": "2025-06-01T12:00:00Z"
}


class MockRegistryHandler(BaseHTTPRequestHandler):
    server_version = "OOHDI/0.1 MockRegistry"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.strip("/")
        segments = [segment for segment in path.split("/") if segment]

        if len(segments) == 1 and segments[0] == "oohdi":
            self._send_json(400, {"error_code": "bad_request", "message": "Missing namespace."})
            return

        if len(segments) >= 2 and segments[0] == "oohdi":
            namespace = segments[1]
            if len(segments) == 2:
                self._send_json(200, {
                    "id": f"{namespace}/oohdi",
                    "organization": "Foobar Outdoor Media",
                    "website": "https://foobaroutdoor.com",
                    "created_at": "2025-01-01T12:00:00Z",
                    "updated_at": "2025-06-01T12:00:00Z"
                })
                return

            if len(segments) == 3:
                payload = dict(EXAMPLE_RECORD)
                payload["identity"] = dict(payload["identity"])
                payload["identity"]["id"] = f"{namespace}/oohdi/{segments[2]}"
                self._send_json(200, payload)
                return

        self._send_json(404, {"error_code": "not_found", "message": "Resource not found."})

    def _send_json(self, status_code: int, payload: Dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:
        return


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = HTTPServer((host, port), MockRegistryHandler)
    print(f"Mock OOHDI registry running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start a local mock OOHDI registry for development and tests.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    run_server(args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
