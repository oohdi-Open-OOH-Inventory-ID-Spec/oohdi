# Registry Setup Guide

This guide explains the basic requirements for a company that wants to operate a screen registry that follows the OOHDI model used in this repository.

It covers the minimum operational setup, the required public endpoints, the JSON structures, a simple database model, and a sample import package that can be used for testing.

---

## 1. What a registry provider must provide

A company building a screen registry must operate a public, HTTPS-based registry service that is authoritative for a specific media-owner namespace.

At minimum, the company must provide:

- A public DNS hostname such as `registry.example.com`
- A media-owner domain such as `example.com` or `foobaroutdoor.com`
- An `_oohdi.<domain>` DNS TXT record indicating the authoritative registry
- A public read-only registry API
- A storage layer for media-owner and screen records
- Data validation, versioning, and error handling
- Monitoring, rate limiting, and operational support

A registry is not a general search service. The OOHDI model is designed around authoritative public read access to a known identifier, not bulk enumeration.

---

## 2. DNS and authority requirements

For each media owner domain, the company must publish a single authoritative registry declaration.

### DNS TXT example

```
TXT _oohdi.foobaroutdoor.com
v=OOHDI1; r=registry.foobaroutdoor.com;
```

This means:

- `v` identifies the OOHDI major version
- `r` identifies the authoritative registry hostname
- Only one registry should be declared for that namespace at a time

### Important rules

- The registry host must be a DNS hostname, not a full URL
- The value must be a bare hostname, such as `registry.example.com`
- The registry must serve content over HTTPS
- The registry should return `421 Misdirected Request` when called for a namespace it does not own

---

## 3. Minimum public endpoints and ports

### Production network exposure

Typical production exposure:

- `443/tcp` – public HTTPS registry API
- `80/tcp` – optional redirect to HTTPS
- `443/tcp` from the external internet to the registry service

For local development or testing, a service may run on a non-standard port such as `8080` or `18080`, but production should use standard HTTPS on port `443`.

### Required read-only HTTP endpoints

The registry should provide these public read endpoints:

#### Organization or media-owner record

```
GET https://<DISPLAY_REGISTRY_DNS_NAME>/oohdi/<REVERSE_DNS_NAME>
```

Example:

```
GET https://registry.foobaroutdoor.com/oohdi/com.foobaroutdoor
```

#### Sellable inventory unit record

```
GET https://<DISPLAY_REGISTRY_DNS_NAME>/oohdi/<REVERSE_DNS_NAME>/<MEDIA_OWNER_DISPLAY_ID>
```

Example:

```
GET https://registry.foobaroutdoor.com/oohdi/com.foobaroutdoor/oohdi/emp-001
```

### Optional operational endpoints

These are helpful but not part of the required OOHDI public contract:

```
GET /health
GET /
```

Example health response:

```json
{
  "status": "ok"
}
```

---

## 4. Required registry behavior

A registry must:

- Reply with `200 OK` for valid records
- Reply with `404 Not Found` when the record does not exist
- Reply with `410 Gone` when a record is permanently removed
- Reply with `301 Moved Permanently` when an identifier has changed
- Reply with `421 Misdirected Request` for non-authoritative namespaces
- Return public JSON payloads, not HTML pages
- Operate without authentication for read access

### Misdirected request example

```json
{
  "error_code": "not_authoritative",
  "message": "This registry is not authoritative for the requested media owner namespace.",
  "authoritative_registry_hint": "registry.example.com"
}
```

---

## 5. Sample JSON schema for a registry

Below are example payloads based on the structures used by this repo.

### 5.1 Media owner record schema

```json
{
  "id": "com.foobaroutdoor/oohdi",
  "organization": "Foobar Outdoor Media",
  "street_address": "123 Main St",
  "city": "New York",
  "region": "NY",
  "country": "US",
  "phone_number": "+1-212-555-1212",
  "email_address": "support@foobaroutdoor.com",
  "website": "https://foobaroutdoor.com",
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-06-01T12:00:00Z"
}
```

### 5.2 Screen inventory record schema

```json
{
  "identity": {
    "id": "com.foobaroutdoor/oohdi/emp-001",
    "name": "Harborview Digital 01",
    "description": "Digital display facing Harbor Avenue"
  },
  "state": {
    "type": "digital",
    "status": "active"
  },
  "inventory": {
    "unit_type": "display"
  },
  "location": {
    "location_type": "fixed",
    "point": {
      "latitude": 45.5231,
      "longitude": -122.6765
    },
    "bounds": null
  },
  "physical": {
    "dimensions": {
      "units": "feet",
      "width": 24,
      "height": 12,
      "bottom_elevation": 18.0
    },
    "orientation": {
      "azimuth": 90,
      "pitch": 0
    },
    "viewer": {
      "context": "vehicular",
      "reads": "R"
    }
  },
  "device": {
    "dimensions": {
      "units": "pixels",
      "width": 1920,
      "height": 1080
    },
    "player": {
      "platform": "ExamplePlayer",
      "version": "9.3.1"
    }
  },
  "capabilities": {
    "media_formats": [
      {
        "type": "digital_image",
        "enabled": true,
        "min_duration_seconds": 8,
        "max_duration_seconds": 8
      },
      {
        "type": "digital_video",
        "enabled": true,
        "min_duration_seconds": 8,
        "max_duration_seconds": 30
      }
    ]
  },
  "taxonomy": {
    "venue_type_id": "openooh:venue:301"
  },
  "extensions": {},
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-06-15T10:00:00Z"
}
```

---

## 6. Recommended database schema

A simple production-ready design can be implemented with PostgreSQL and JSONB for flexible fields.

### Media owners table

```sql
CREATE TABLE media_owners (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  namespace TEXT NOT NULL UNIQUE,
  organization_name TEXT NOT NULL,
  legal_name TEXT,
  street_address TEXT,
  city TEXT,
  region TEXT,
  country CHAR(2),
  phone_number TEXT,
  email_address TEXT,
  website TEXT NOT NULL,
  canonical_id TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Screen inventory table

```sql
CREATE TABLE screen_inventory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  media_owner_id UUID NOT NULL REFERENCES media_owners(id),
  canonical_id TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  description TEXT,
  state_type TEXT NOT NULL,
  state_status TEXT NOT NULL,
  inventory_unit_type TEXT,
  parent_unit_id TEXT,
  location_type TEXT NOT NULL,
  latitude NUMERIC(9,7),
  longitude NUMERIC(10,7),
  bounds JSONB,
  physical JSONB,
  device JSONB,
  capabilities JSONB,
  taxonomy JSONB,
  extensions JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Optional audit table

```sql
CREATE TABLE registry_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  screen_id UUID REFERENCES screen_inventory(id),
  event_type TEXT NOT NULL,
  payload JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Data rules

- `canonical_id` must be the final lowercase OOHDI identifier
- `namespace` should match the media-owner reverse-DNS namespace
- `parent_unit_id` should be a valid canonical identifier when provided
- `bounds` should be stored as GeoJSON when the record is mobile
- `capabilities` and `extensions` are good candidates for `JSONB`

---

## 7. Sample import data

A sample JSON file for registry testing is available here:

- [sample-registry-import.json](sample-registry-import.json)

This file contains a small set of example records and is intended to be used as a quick import baseline for a test registry.

### Example import payload

```json
[
  {
    "identity": {
      "id": "org.oohdi.example-media-owner/oohdi/emp-001",
      "name": "Harborview Digital 01",
      "description": "Digital display facing Harbor Avenue"
    },
    "state": {"type": "digital", "status": "active"},
    "inventory": {"unit_type": "display"},
    "location": {
      "location_type": "fixed",
      "point": {"latitude": 45.5231, "longitude": -122.6765},
      "bounds": null
    },
    "physical": {
      "dimensions": {"units": "feet", "width": 24, "height": 12, "bottom_elevation": 18.0},
      "orientation": {"azimuth": 90, "pitch": 0},
      "viewer": {"context": "vehicular", "reads": "R"}
    },
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-06-15T10:00:00Z"
  }
]
```

---

## 8. How to test the registry with sample data

### Local example registry

The repository includes a fictional registry example that can be used for testing.

Start it locally:

```bash
cd /home/ekubischta/oohdi/examples/fictional_registry
OOHDI_PORT=8080 python3 app.py
```

Then test the endpoints:

```bash
curl -sS http://127.0.0.1:8080/health
curl -sS http://127.0.0.1:8080/oohdi/org.oohdi.example-media-owner
curl -sS http://127.0.0.1:8080/oohdi/org.oohdi.example-media-owner/oohdi/emp-001
```

Expected behavior:

- `/oohdi/org.oohdi.example-media-owner` should return the media-owner record
- `/oohdi/org.oohdi.example-media-owner/oohdi/emp-001` should return the sample screen record
- a mismatched namespace should return `421 Misdirected Request`

### Example production-style checks

```bash
curl -sS -D - https://registry.foobaroutdoor.com/oohdi/com.foobaroutdoor
curl -sS -D - https://registry.foobaroutdoor.com/oohdi/com.foobaroutdoor/oohdi/emp-001
```

### Testing imported records

After importing your sample records, verify:

1. The media owner endpoint returns the correct organization
2. The screen endpoint returns the screen metadata
3. Missing IDs return `404 Not Found`
4. Wrong namespace returns `421 Misdirected Request`
5. Updates preserve canonical IDs and timestamps

---

## 9. Implementation checklist

Use this checklist when standing up a registry:

- [ ] Register the registry hostname in DNS
- [ ] Publish `_oohdi.<media_owner_domain>` TXT record
- [ ] Configure HTTPS certificates for the registry host
- [ ] Expose `443/tcp` publicly
- [ ] Build `/oohdi/<namespace>` and `/oohdi/<namespace>/<id>` endpoints
- [ ] Implement canonical ID validation
- [ ] Store media-owner and screen records in a database
- [ ] Validate against required JSON fields
- [ ] Support `200`, `301`, `304`, `404`, `410`, and `421` states
- [ ] Load sample data and test using real API calls
- [ ] Add rate limiting, caching, and monitoring

---

## 10. Recommended startup approach

A new registry provider should start with:

1. One authoritative domain
2. One registry host
3. One media owner namespace
4. A small known sample data set
5. A validation and smoke-test script

Once the API works with the sample imports and DNS tests, the provider can expand to full operational data pipelines and more complex inventory workflows.

---

## 11. Summary

A registry company does not need a complicated global network to get started. The minimum viable registry is a public HTTPS service that:

- answers authoritative OOHDI namespace requests,
- returns valid media-owner and screen JSON payloads,
- exposes the two public OOHDI read endpoints,
- publishes the correct DNS TXT record,
- and can be tested against sample data.

This repository already provides an example of the intended shape for that data and API.
