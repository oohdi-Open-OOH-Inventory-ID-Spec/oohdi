# OOHDI Website Demo

This folder contains a small one-page OOHDI website that lets you enter an OOHDI identifier and validates the format, DNS TXT record, and registry lookup behavior.

## Prerequisites

- Docker
- Docker Compose
- A working local OOHDI repo checkout

## Start the website

From the repo root:

```bash
cd /home/ekubischta/oohdi
docker compose -f website/docker-compose.yml up --build
```

The site will be available at:

```text
http://localhost:18082/
```

## Alternative local run without Docker

From the repo root:

```bash
cd /home/ekubischta/oohdi
python3 -m venv .venv
. .venv/bin/activate
python -m pip install dnspython
cd website
OOHDI_PORT=18082 python app.py
```

Then open:

```text
http://127.0.0.1:18082/
```

## Example validation

Try an identifier such as:

```text
org.oohdi.example-media-owner/oohdi/emp-001
```

This will validate the format and show the DNS/TXT and registry lookup status.

## Notes

- The page expects a valid `_oohdi.<domain>` TXT record for the owner domain when checking a real identifier.
- The example registry service in the repo can be used to test a successful registry fetch flow.
