# Registry Quickstart

This is the short version of the registry setup guide for a company that wants to run an OOHDI-compatible screen registry.

## 1. Minimum requirements

A registry provider needs:

- A public DNS hostname, for example `registry.example.com`
- A media-owner domain, for example `foobaroutdoor.com`
- A valid `_oohdi.<media_owner_domain>` DNS TXT record
- HTTPS-only public read endpoints
- A database to store media-owner and screen records
- Validation for record IDs, timestamps, and status codes

## 2. Required DNS record

Publish this in DNS:

```dns
TXT _oohdi.foobaroutdoor.com
v=OOHDI1; r=registry.foobaroutdoor.com;
```

The `r` field must point to the authoritative registry hostname, not a URL.

## 3. Required public endpoints

Expose these read-only endpoints on HTTPS:

```text
GET https://registry.example.com/oohdi/<REVERSE_DNS_NAME>
GET https://registry.example.com/oohdi/<REVERSE_DNS_NAME>/<MEDIA_OWNER_DISPLAY_ID>
```

Examples:

```text
GET https://registry.foobaroutdoor.com/oohdi/com.foobaroutdoor
GET https://registry.foobaroutdoor.com/oohdi/com.foobaroutdoor/oohdi/emp-001
```

### Standard ports

- `443/tcp` for public HTTPS registry traffic
- `80/tcp` optional redirect to HTTPS

## 4. Required response patterns

The registry must return:

- `200 OK` for valid records
- `404 Not Found` for missing records
- `410 Gone` for permanently removed records
- `301 Moved Permanently` for re-identified records
- `421 Misdirected Request` when the namespace is not authoritative

Example error response:

```json
{
  "error_code": "not_authoritative",
  "message": "This registry is not authoritative for the requested media owner namespace.",
  "authoritative_registry_hint": "registry.example.com"
}
```

## 5. Sample record format

### Media owner record

```json
{
  "id": "com.foobaroutdoor/oohdi",
  "organization": "Foobar Outdoor Media",
  "website": "https://foobaroutdoor.com",
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-06-01T12:00:00Z"
}
```

### Screen record

```json
{
  "identity": {
    "id": "com.foobaroutdoor/oohdi/emp-001",
    "name": "Harborview Digital 01"
  },
  "state": {
    "type": "digital",
    "status": "active"
  },
  "location": {
    "location_type": "fixed",
    "point": {
      "latitude": 45.5231,
      "longitude": -122.6765
    }
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-06-15T10:00:00Z"
}
```

## 6. Basic database structure

```sql
CREATE TABLE media_owners (
  id UUID PRIMARY KEY,
  namespace TEXT UNIQUE NOT NULL,
  canonical_id TEXT UNIQUE NOT NULL,
  organization_name TEXT NOT NULL,
  website TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE screen_inventory (
  id UUID PRIMARY KEY,
  media_owner_id UUID REFERENCES media_owners(id),
  canonical_id TEXT UNIQUE NOT NULL,
  display_name TEXT NOT NULL,
  state_type TEXT NOT NULL,
  state_status TEXT NOT NULL,
  location_type TEXT NOT NULL,
  latitude NUMERIC(9,7),
  longitude NUMERIC(10,7),
  physical JSONB,
  device JSONB,
  capabilities JSONB,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
```

## 7. How to test the registry

Run a local example service using the repo’s fictional registry:

```bash
cd /home/ekubischta/oohdi/examples/fictional_registry
OOHDI_PORT=8080 python3 app.py
```

Then test:

```bash
curl -sS http://127.0.0.1:8080/health
curl -sS http://127.0.0.1:8080/oohdi/org.oohdi.example-media-owner
curl -sS http://127.0.0.1:8080/oohdi/org.oohdi.example-media-owner/oohdi/emp-001
```

This should return JSON for the media owner and one screen record.

## 8. Sample data import

A sample import file is available here:

- [sample-registry-import.json](sample-registry-import.json)

Use it as a baseline for validating your registry logic before importing production inventory.

## 9. Practical checklist

- [ ] Publish the DNS TXT record
- [ ] Expose HTTPS on port 443
- [ ] Implement the media-owner endpoint
- [ ] Implement the screen endpoint
- [ ] Validate canonical IDs and timestamps
- [ ] Return correct status codes
- [ ] Import sample records and test live responses
- [ ] Add monitoring and rate limiting

## 10. Summary

The minimum viable OOHDI registry is a public HTTPS service that serves valid JSON records for a single media-owner namespace and declares that authority via DNS. Once the DNS record and endpoints work, the rest of the registry can be expanded with more inventory and operational tooling.
