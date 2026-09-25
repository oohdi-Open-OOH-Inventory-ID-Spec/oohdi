import json
import os
import re
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import urllib.error
from urllib.request import Request, urlopen

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(os.path.dirname(ROOT), "img")

LOGO_PATH = os.path.join(IMG_DIR, "oohdi-logo-large.png")

SPEC_GITHUB = "https://github.com/oohdi-Open-OOH-Inventory-ID-Spec/oohdi"
GUIDE_INDEX = SPEC_GITHUB + "/blob/main/guides/index.md"
MEDIA_OWNER_GUIDE = SPEC_GITHUB + "/blob/main/guides/media-owner-setup-guide.md"
REGISTRY_GUIDE = SPEC_GITHUB + "/blob/main/guides/registry-setup-guide.md"
REGISTRY_QUICKSTART = SPEC_GITHUB + "/blob/main/guides/registry-quickstart.md"

OOHDI_COLOR_DARK = "#0d2d54"
OOHDI_COLOR_TEAL = "#4fe0d8"
OOHDI_COLOR_LIGHT = "#dfeaf6"
OOHDI_COLOR_BG = "#050f1a"
OOHDI_COLOR_MUTED = "#7aa1c1"

VALID_ID_PATTERN = re.compile(r"^[a-z0-9._~-]+/oohdi/[a-z0-9._~-]+$")


def canonicalize_identifier(identifier: str) -> str:
    if identifier is None:
        raise ValueError("Identifier is required.")
    value = str(identifier).strip().lower().rstrip("/")
    if not value or value.startswith("/"):
        raise ValueError("Identifier is invalid.")
    if value.count("/oohdi/") != 1:
        raise ValueError("Identifier must contain exactly one /oohdi/ segment.")
    if len(value) > 255:
        raise ValueError("Identifier exceeds 255 characters.")
    if not VALID_ID_PATTERN.fullmatch(value):
        raise ValueError("Identifier contains invalid characters.")
    return value


def probe_txt_record(domain: str):
    try:
        import dns.resolver
        answers = dns.resolver.resolve(f"_oohdi.{domain}", "TXT")
        records = []
        for answer in answers:
            records.append(str(answer).strip('"'))
        return {"ok": True, "records": records}
    except Exception as exc:
        return {"ok": False, "error": str(exc) }


def build_registry_url(registry_host: str, identifier: str) -> str:
    host = registry_host.strip().rstrip("/")
    if host.startswith("http://") or host.startswith("https://"):
        base = host
    else:
        if ":" in host and not host.startswith("["):
            base = f"http://{host}"
        else:
            base = f"https://{host}"

    canonical = canonicalize_identifier(identifier)
    namespace, media_owner_id = canonical.rsplit("/oohdi/", 1)
    return f"{base}/oohdi/{namespace}/{media_owner_id}"


def fetch_registry_record(registry_host: str, identifier: str):
    try:
        canonical = canonicalize_identifier(identifier)
        url = build_registry_url(registry_host, canonical)
        req = Request(url, headers={"Accept": "application/json"})
        with urlopen(req, timeout=12) as resp:
            body = resp.read().decode("utf-8")
            payload = json.loads(body) if body else {}
            return {"ok": True, "url": url, "status": resp.status, "payload": payload}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            payload = {"raw": body}
        return {
            "ok": False,
            "url": url,
            "status": exc.code,
            "payload": payload,
            "error": str(exc),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def evaluate_identifier(identifier: str):
    result = {"identifier": identifier, "canonical": None, "valid": False, "errors": [], "warnings": [], "txt": None, "registry": None, "response": None }

    try:
        result["canonical"] = canonicalize_identifier(identifier)
        result["valid"] = True
    except ValueError as exc:
        result["errors"].append(str(exc))
        return result

    parts = result["canonical"].split("/oohdi/")
    if len(parts) != 2:
        result["errors"].append("Identifier does not match the required reverse-DNS/oohdi format.")
        return result

    reverse_domain = parts[0]
    domain = reverse_domain.split(".")
    if len(domain) < 2:
        result["errors"].append("Reverse DNS namespace must include a domain hierarchy.")

    domain_name = ".".join(reversed(reverse_domain.split(".")))
    txt = probe_txt_record(domain_name)
    result["txt"] = txt
    if not txt["ok"]:
        result["errors"].append("No valid _oohdi TXT record found for the media owner domain.")
    else:
        records = txt["records"]
        registry = None
        for entry in records:
            if entry.startswith("v=OOHDI1"):
                match = re.search(r"r=([^;]+)", entry, re.IGNORECASE)
                if match:
                    registry = match.group(1).strip()
                    break
        result["registry"] = registry
        if registry is None:
            result["errors"].append("TXT record is present but missing a valid r= registry declaration.")

    if result["registry"]:
        reg_response = fetch_registry_record(result["registry"], result["canonical"])
        result["response"] = reg_response
        if not reg_response["ok"]:
            result["errors"].append(f"Registry lookup failed: {reg_response['error']}")
        else:
            if reg_response["status"] == 421:
                result["errors"].append("Registry returned 421 Misdirected Request: not_authoritative.")
            elif reg_response["status"] == 404:
                result["errors"].append("Record was not found in the authoritative registry.")
            elif reg_response["status"] == 410:
                result["errors"].append("Record is gone and no replacement is available.")
            elif reg_response["status"] == 301:
                result["warnings"].append("Registry returned 301 redirect to a new canonical record.")

    return result


def render_shim_html(title: str, body_html: str, request_value: str = ""):
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>{title}</title>
  <style>
    :root {{
      --bg: {OOHDI_COLOR_BG};
      --dark: {OOHDI_COLOR_DARK};
      --teal: {OOHDI_COLOR_TEAL};
      --light: {OOHDI_COLOR_LIGHT};
      --muted: {OOHDI_COLOR_MUTED};
      --panel: rgba(13, 45, 84, 0.84);
      --panel-border: rgba(79, 224, 216, 0.3);
      --danger: #ff7a7a;
      --warning: #ffd166;
      --success: #7ef0b8;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; background: var(--bg); color: var(--light); }}
    body {{ line-height: 1.5; }}
    a {{ color: var(--teal); }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 48px 24px 80px; }}
    .brand {{ text-align: center; margin-bottom: 18px; }}
    .brand img {{ width: min(900px, 100%); height: auto; display: block; margin: 0 auto; }}
    .box {{ background: rgba(13, 45, 84, 0.7); border: 1px solid var(--panel-border); border-radius: 18px; padding: 22px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
    .search-row {{ display: flex; gap: 12px; flex-wrap: wrap; }}
    input[type=text] {{ flex: 1; min-width: 240px; border: 1px solid rgba(79,224,216,0.4); background: rgba(255,255,255,0.04); color: var(--light); border-radius: 12px; padding: 16px 18px; font-size: 1.05rem; }}
    button {{ background: linear-gradient(135deg, var(--teal), #6de8f0); color: var(--dark); border: 0; border-radius: 12px; padding: 16px 22px; font-size: 1rem; font-weight: 700; cursor: pointer; }}
    .status {{ margin-top: 18px; padding: 14px 16px; border-radius: 12px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); }}
    .status h3 {{ margin: 0 0 8px; font-size: 1rem; letter-spacing: 0.04em; text-transform: uppercase; color: var(--teal); }}
    .result {{ margin-top: 24px; white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; background: rgba(3, 8, 14, 0.7); border: 1px solid rgba(79,224,216,0.18); border-radius: 12px; padding: 18px; overflow: auto; }}
    .section {{ margin-top: 38px; }}
    .two-col {{ display: grid; grid-template-columns: 1.3fr 0.7fr; gap: 24px; }}
    @media (max-width: 820px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
    .card {{ background: rgba(13, 45, 84, 0.7); border: 1px solid var(--panel-border); border-radius: 18px; padding: 22px; }}
    h1, h2, h3, p {{ margin-top: 0; }}
    .example-list {{ margin: 0; padding-left: 1.25rem; }}
    .example-list li {{ margin: 10px 0; font-size: 1.2rem; line-height: 1.45; color: var(--light); }}
    .example-list code {{ font-size: 1.15em; font-weight: 700; color: #bffaf5; background: rgba(79, 224, 216, 0.12); padding: 3px 7px; border-radius: 8px; }}
    .tag {{ display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: bold; color: var(--dark); background: var(--teal); }}
    .error-list {{ color: var(--danger); }}
    .warning-list {{ color: var(--warning); }}
    .success {{ color: var(--success); }}
    .muted {{ color: var(--muted); }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"brand\">
      <img src=\"/logo\" alt=\"OOHDI logo\" />
    </div>
    <div class=\"box\">
      <form method=\"GET\" action=\"/\">
        <div class=\"search-row\">
          <input type=\"text\" name=\"id\" value=\"{html_escape(request_value)}\" placeholder=\"Enter an OOHDI-compatible display ID\" />
          <button type=\"submit\">Check ID</button>
        </div>
      </form>
      {body_html}
    </div>

    <div class=\"section two-col\">
      <div class=\"card\">
        <h2>Why OOHDI exists</h2>
        <p>OOHDI creates an open source, globally unique, decentralized identifier for sellable out-of-home inventory. It helps buyers, sellers, creative teams, and media operators identify the same display consistently across fragmented systems.</p>
        <p>Without a common identifier, inventory is hard to discover, verify, validate, and de-duplicate across SSPs, DSPs, CMS platforms, and media owner systems.</p>
      </div>
      <div class=\"card\">
        <h2>Who it is for</h2>
        <ul>
          <li>Media owners</li>
          <li>SSPs and DSPs</li>
          <li>Agencies and buyers</li>
          <li>Creative teams</li>
          <li>OOH registry and ad-tech providers</li>
        </ul>
      </div>
    </div>
    <div class="section two-col">
      <div class="card">
        <h2>Example OOHDI identifiers</h2>
        <p>OOHDI identifiers follow a reverse-DNS namespace and a canonical inventory path.</p>
        <ul class="example-list">
          <li><code>com.foobaroutdoor/oohdi/ab-1234-c</code></li>
          <li><code>uk.co.barfoodmedia/oohdi/98765</code></li>
        </ul>
      </div>
      <div class="card">
        <h2>What is a registry?</h2>
        <p>A registry is the authoritative public service that exposes inventory data for a media owner namespace. It is the source of truth for screen records, metadata, and canonical OOHDI identifiers.</p>
        <p>Registry discovery happens through DNS, using an <code>_oohdi.&lt;domain&gt;</code> TXT record that points to the authoritative registry host.</p>
      </div>
    </div>

    <div class="section">
      <div class="card">
        <h2>Who owns OOHDI?</h2>
        <p>OOHDI is decentralized with no owner organization. It operates on principles of DNS and is designed to ensure no single entity controls IDs.</p>
      </div>
    </div>

    <div class="section">
      <div class="card">
        <h2>Who should build registries?</h2>
        <p>The following companies should consider exposing their inventory via an OOHDI compatible registry:</p>
        <ul>
          <li>Digital Signage CMS systems</li>
          <li>Digital Signage player systems and CRM systems</li>
          <li>Static billboard inventory systems</li>
          <li>Medium to Large OOH companies that maintain their own source of inventory truth</li>
        </ul>
      </div>
    </div>

    <div class="section">
      <div class="card">
        <h2>Getting started guides</h2>
        <div class="two-col">
          <div>
            <h3>Overview</h3>
            <ul>
              <li><a href="{GUIDE_INDEX}" target="_blank" rel="noreferrer">Guide index</a></li>
            </ul>
          </div>
          <div>
            <h3>For media owners</h3>
            <ul>
              <li><a href="{MEDIA_OWNER_GUIDE}" target="_blank" rel="noreferrer">Media owner setup guide</a></li>
            </ul>
          </div>
          <div>
            <h3>For registry owners</h3>
            <ul>
              <li><a href="{REGISTRY_GUIDE}" target="_blank" rel="noreferrer">Registry setup guide</a></li>
              <li><a href="{REGISTRY_QUICKSTART}" target="_blank" rel="noreferrer">Registry quickstart</a></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    <div class="section">
      <div class="card">
        <h2>Request for Comments</h2>
        <p>This is a DRAFT proposal for public review. Comments should be submitted either as issue comments on the GitHub repository or as pull requests on the GitHub repository.</p>
        <p><a href="{SPEC_GITHUB}" target="_blank" rel="noreferrer">Open OOHDI GitHub repository</a></p>
        <p><a href="{SPEC_GITHUB}/issues" target="_blank" rel="noreferrer">Submit an issue comment</a> | <a href="{SPEC_GITHUB}/pulls" target="_blank" rel="noreferrer">Submit a pull request</a></p>
      </div>
    </div>
    <div class="section">
      <div class="card">
        <h2>More information</h2>
        <p>The full OOHDI specification, examples, and code are available in the project repository.</p>
        <p><a href="{SPEC_GITHUB}" target="_blank" rel="noreferrer">Open OOHDI GitHub repository</a></p>
      </div>
    </div>
  </div>
</body>
</html>
"""


def html_escape(value: str) -> str:
    if value is None:
        return ""
    return (
        str(value).replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


class OOHDIWebsiteHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/logo":
            try:
                with open(LOGO_PATH, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception:
                self.send_response(404)
                self.end_headers()
                return

        query = parse_qs(parsed.query)
        raw_id = query.get("id", [""])[0]
        if not raw_id:
            body = (
                "<div class=\"status\">"
                "<h3>Ready</h3>"
                "<p class=\"muted\">Enter an OOHDI-compatible screen ID to validate it against the specification.</p>"
                "<p class=\"muted\">Try <code>org.oohdi.example-media-owner/oohdi/emp-001</code> as an example valid OOHDI.</p>"
                "</div>"
            )
            self._send(render_shim_html("OOHDI: Out Of Home Display Identifier Specification", body, raw_id))
            return

        report = evaluate_identifier(raw_id)

        lines = []
        lines.append("<div class=\"status\">")
        lines.append("<h3>Validation Result</h3>")
        lines.append(f"<p><span class=\"tag\">{html_escape(report['canonical'] or report['identifier'])}</span></p>")

        if report["valid"]:
            lines.append("<p class=\"success\">Identifier format is valid.</p>")
        else:
            lines.append("<p class=\"error-list\">Identifier format is invalid.</p>")

        if report["errors"]:
            lines.append("<div class=\"error-list\"><strong>Errors:</strong><ul>")
            for msg in report["errors"]:
                lines.append(f"<li>{html_escape(msg)}</li>")
            lines.append("</ul></div>")

        if report["warnings"]:
            lines.append("<div class=\"warning-list\"><strong>Warnings:</strong><ul>")
            for msg in report["warnings"]:
                lines.append(f"<li>{html_escape(msg)}</li>")
            lines.append("</ul></div>")

        if report["txt"]:
            lines.append(f"<div><strong>TXT record:</strong> {html_escape(json.dumps(report['txt'], indent=2, sort_keys=True))}</div>")

        if report["registry"]:
            lines.append(f"<div><strong>Registry:</strong> {html_escape(report['registry'])}</div>")

        if report["response"]:
            lines.append(f"<div><strong>Registry response:</strong><br><pre>{html_escape(json.dumps(report['response'], indent=2, sort_keys=True))}</pre></div>")

        lines.append("</div>")
        body = "\n".join(lines)
        self._send(render_shim_html("OOHDI: Out Of Home Display Identifier Specification", body, raw_id))

    def _send(self, html: str):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        return


if __name__ == "__main__":
    host = os.environ.get("OOHDI_HOST", "0.0.0.0")
    port = int(os.environ.get("OOHDI_PORT", "8080"))
    server = HTTPServer((host, port), OOHDIWebsiteHandler)
    print(f"OOHDI website running at http://{host}:{port}")
    server.serve_forever()
