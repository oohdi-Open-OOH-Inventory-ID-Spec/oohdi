# Guide for Agent Registry Builders

This guide is intended for coding agents, LLMs, and implementation teams working with a third-party company that wants to add OOHDI-compatible registry endpoints to an existing platform.

The goal is not to invent a new registry system from scratch. The goal is to integrate OOHDI semantics into the company’s current architecture without breaking existing inventory, media-owner, or CRM systems.

This document complements the main OOHDI specification in the repository and the setup guides in this folder.

---

## 1. Who this is for

This guide is for teams that are:

- Adding OOHDI read endpoints to an existing ad-tech, media-owner, or registry platform
- Operating a registry for one or more media-owner namespaces
- Integrating OOHDI with existing CMS, inventory, or asset management systems
- Building a public registry service that sits behind a DNS-authoritative domain
- Creating a service that must interoperate with other OOHDI-compatible registries

This is usually not a greenfield project. In most real deployments, the company already has a platform, a database, an API layer, and operational tooling. The OOHDI work is a compatibility layer on top of that platform.

---

## 2. Core purpose of OOHDI

The OOHDI specification defines a globally unique, decentralized identifier for sellable inventory units in out-of-home media.

At a high level, the registry model is:

- A media owner controls a reverse-DNS namespace such as `com.foobaroutdoor`
- That media owner publishes a DNS TXT record declaring the authoritative registry
- A public HTTPS registry serves JSON records for that namespace
- Clients resolve a known identifier and retrieve canonical metadata

The public contract is intentionally small and read-only. It is designed for identifier validation, metadata verification, and synchronization, not for broad listing or bulk inventory enumeration.

Important design principle:

- The identifier is stable
- The metadata may change
- The registry is authoritative for a namespace
- The registry is public, read-only, and discoverable via DNS

---

## 3. What the agent should confirm before implementing

Before writing code, the agent should ask the developer a short set of questions that determine the real integration shape.

### 3.1 Domain and authority questions

Ask the company:

- What is the media-owner domain we are authoritatively representing?
- Is the domain already owned and controlled by the company?
- Is the company operating a shared registry for multiple media owners or a single owner?
- Do we need support for multiple namespaces under a single registry host?
- What is the exact DNS hostname for the registry service?
- Can we publish the `_oohdi.<domain>` TXT record in the company’s DNS zone?
- Are there delegated sub-brands or business units with their own domains?

### 3.2 Existing platform questions

Ask:

- What system currently stores the inventory records?
- Is there already an inventory API, CMS, or database schema we should map into OOHDI records?
- Are media owner records already modeled in the platform?
- Are the existing IDs stable, human-readable, or only internal keys?
- Can we derive a canonical OOHDI identifier from an existing inventory ID without changing the underlying record IDs?
- Is there already a concept of parent units, hierarchical inventory, or screen segments?

### 3.3 Data model questions

Ask:

- What fields already exist for display name, status, location, geometry, and physical dimensions?
- Do we have digital, static, and print display types?
- Are we dealing with fixed displays, mobile inventory, or both?
- Can we represent `fixed` vs `mobile` location semantics in the current model?
- Which fields are already public vs which are sensitive and should not be exposed?
- Do we have a concept of `created_at` and `updated_at` for inventory updates?

### 3.4 Operational questions

Ask:

- Will this registry be public internet-facing?
- Do we already have TLS, CDN, WAF, load balancer, and DDoS protection?
- Where do we want to host the registry: separate service, same app, or behind an existing API gateway?
- Which environment is authoritative: production only, or staging + production?
- Do we need caching, rate limiting, or request tracing?
- Who owns DNS changes, certificate renewal, and production deployment?

### 3.5 Compatibility and migration questions

Ask:

- Are there existing IDs that must remain stable for historical clients?
- Do we need 301 redirects for renamed or replaced screens?
- Is there a need to support `410 Gone` for permanently retired inventory?
- Can we map old media-owner IDs into a reverse-DNS namespace cleanly?
- Is there existing data that would violate the canonical lowercase and unreserved-character rules?

---

## 4. What must the company implement

A company building an OOHDI-compatible registry must provide the following core components.

### 4.1 Authoritative DNS declaration

For every media-owner domain, the company must publish a TXT record of the form:

```dns
TXT _oohdi.foobaroutdoor.com
v=OOHDI1; r=registry.foobaroutdoor.com;
```

This is the public trust anchor. It tells clients which registry is authoritative for that ownership namespace.

The company must ensure:

- only one registry is declared at a time
- `r` is a hostname, not a full URL
- the registry host serves content over HTTPS
- the DNS entry is updated when registry ownership changes

### 4.2 Public HTTPS registry service

The registry must be:

- HTTPS-only for public clients
- read-only for unauthenticated consumers
- accessible on the public internet
- authoritative for the configured namespace or namespaces

The service can be implemented inside an existing app, but the public contract must remain consistent with OOHDI semantics, not necessarily the company’s internal API naming.

### 4.3 Public read endpoints

The company must expose:

- media-owner information endpoint
- sellable inventory unit information endpoint

The canonical patterns are:

```text
GET https://<DISPLAY_REGISTRY_DNS_NAME>/oohdi/<REVERSE_DNS_NAME>
GET https://<DISPLAY_REGISTRY_DNS_NAME>/oohdi/<REVERSE_DNS_NAME>/<MEDIA_OWNER_DISPLAY_ID>
```

Examples:

```text
GET https://registry.foobaroutdoor.com/oohdi/com.foobaroutdoor
GET https://registry.foobaroutdoor.com/oohdi/com.foobaroutdoor/oohdi/emp-001
```

### 4.4 Correct status code behavior

The implementation should support the status codes required by OOHDI:

- `200 OK` for valid records
- `301 Moved Permanently` for replaced or reidentified records
- `304 Not Modified` when unchanged
- `404 Not Found` for records that never existed in the registry context
- `410 Gone` for permanently removed records without replacement
- `421 Misdirected Request` when the registry is not authoritative for the requested namespace

Also important:

- do not return HTML pages on these endpoints
- do not require authentication for public reads
- return JSON payloads only

---

## 5. Implementation model for existing platforms

Most companies already have a platform, not a blank database. The agent should think in terms of a compatibility layer.

### 5.1 Common existing platform patterns

A third-party company may be operating one of these patterns:

- monolithic app with a route layer and database
- microservices where inventory is managed by a separate service
- CMS with a public API and internal dataset store
- CRM/ERP plus ad-tech inventory backend
- data warehouse with a thin API front-end

The OOHDI registry component can usually be implemented as an adapter layer in front of the existing record storage. The important thing is that the public registry does not leak internal IDs, sensitive fields, or domain-specific structures unless they are intentionally mapped to the OOHDI schema.

### 5.2 Recommended technical approach

The agent should look for these capabilities in the existing stack:

- a canonical identifier builder
- a media-owner domain registry
- a public API route or controller layer
- authoritative data storage
- validation and transformation logic
- HTTP error handling and response shaping
- optional caching and cache invalidation

The implementation should not require rewriting the company’s whole platform. Instead, it should translate:

- internal media owner → OOHDI reverse-DNS namespace
- internal screen ID → OOHDI display identifier
- internal status → `state.status`
- internal display type → `state.type`
- existing geometry data → `location` and `physical` structures

### 5.3 Key integration question

The agent should ask:

- Is the OOHDI registry the source of truth, or is it a public mirror of an internal source of truth?

This answer matters because an OOHDI registry is supposed to be authoritative for a namespace, not merely a visualization of inventory.

---

## 6. Data mapping and canonicalization

The registry must be strict about ID generation and normalization.

### 6.1 Reverse-DNS namespace

The namespace for a media owner should use the reverse DNS form of the authoritative domain, such as:

```text
com.foobaroutdoor
uk.co.barfoodmedia
```

The company must confirm exactly which domain is authoritative and how it should be treated for delegated units.

### 6.2 Canonical identifier rules

All OOHDI identifiers must:

- be lowercase
- use the form `<REVERSE_DNS_NAME>/oohdi/<MEDIA_OWNER_DISPLAY_ID>`
- not include a trailing slash
- not use percent encoding for unreserved characters
- use only RFC 3986 unreserved characters in the local display ID

Examples:

```text
com.foobaroutdoor/oohdi/ab-1234-c
uk.co.barfoodmedia/oohdi/98765
```

The agent should validate that the internal local display ID does not contain characters that are illegal in the OOHDI canonical format.

### 6.3 Media-owner record ID

The media-owner record ID should be:

```text
<REVERSE_DNS_NAME>/oohdi
```

Example:

```text
com.foobaroutdoor/oohdi
```

### 6.4 Date handling

OOHDI expects ISO 8601 / RFC 3339 timestamps such as:

```text
2025-06-01T12:00:00Z
```

The agent should verify the company’s date model and conversion layer, especially if the platform stores timestamps in local timezone or database-specific types.

---

## 7. Required JSON structures

The registry must return JSON records that match OOHDI semantics, even if the company stores data in a different internal shape.

### 7.1 Media-owner object

The public media-owner record should include:

```json
{
  "id": "com.foobaroutdoor/oohdi",
  "organization": "Foobar Outdoor Media",
  "street_address": "123 Main St",
  "city": "New York",
  "region": "NY",
  "country": "US",
  "phone_number": "+1 (212) 555-1212",
  "email_address": "support@foobaroutdoor.com",
  "website": "https://foobaroutdoor.com",
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-06-01T12:00:00Z"
}
```

### 7.2 Inventory object

A screen or sellable-inventory record should include nested objects for identity, state, location, physical characteristics, device metadata, capabilities, and optional extensions.

Example:

```json
{
  "identity": {
    "id": "com.foobaroutdoor/oohdi/abc-1234",
    "name": "Times Square Digital – Upper Panel",
    "description": "Upper sellable segment of Times Square Digital"
  },
  "state": {
    "type": "digital",
    "status": "active"
  },
  "location": {
    "location_type": "fixed",
    "point": {
      "latitude": 40.712776,
      "longitude": -74.005974
    },
    "bounds": null
  },
  "capabilities": {
    "media_formats": [
      {
        "type": "digital_image",
        "enabled": true,
        "min_duration_seconds": 8,
        "max_duration_seconds": 8
      }
    ]
  },
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-06-01T12:00:00Z"
}
```

### 7.3 Important mapping rules

The agent should map data with care:

- `state.type` is one of `digital`, `static`, `print`
- `state.status` is one of `planned`, `active`, `inactive`, `maintenance`, `decommissioned`
- `location.location_type` is `fixed` or `mobile`
- for `fixed`, `bounds` must be null
- for `mobile`, `bounds` must define the operating area
- `capabilities.media_formats` must include at least one entry
- digital formats require duration fields
- static formats should omit duration fields

---

## 8. Non-authoritative handling

A registry may receive requests for namespaces it does not own. In that case it must return a specific error status and payload.

Required behavior:

- `421 Misdirected Request`
- `error_code` = `not_authoritative`
- optionally include `authoritative_registry_hint`

Example:

```json
{
  "error_code": "not_authoritative",
  "message": "This registry is not authoritative for the requested media owner namespace.",
  "authoritative_registry_hint": "registry.example.com"
}
```

If no authoritative registry can be discovered via DNS, the registry must still return `421` and omit the hint.

This is one of the most important implementation details for a company that may host multiple registries or a shared backend.

---

## 9. Lifecycle and integrity rules

The company must decide how to represent inventory history and replacements.

### Required behaviors

- once issued, an OOHDI identifier must not be reassigned to another unit
- for replaced or reidentified units, return `301 Moved Permanently` to the successor canonical identifier
- for permanently removed units with no successor, return `410 Gone`
- `404 Not Found` means the record was not found in the authoritative context

### Implementation notes

The platform may already have a concept of asset replacement or deactivation. The OOHDI registry should map this to the correct status code, not just a generic missing record.

The agent should ask:

- How does the company handle asset replacement, decommissioning, or rebranding?
- Can the platform retain historical identifiers and redirects?
- Is there a separate record for original and successor IDs?

---

## 10. What to ask about the company’s architecture

The following list is a good agent checklist for discovery.

### Platform questions

- Is the registry a thin public API on top of an existing platform, or a separate service?
- Can we add an OOHDI route without affecting internal application contracts?
- What frameworks and languages are in use?
- Does the company already have rate limiters, auth proxies, or API gateways?
- Is there a staging environment that can be used for DNS validation and acceptance tests?

### Data questions

- What is the canonical media-owner identifier today?
- What is the canonical display identifier today?
- Are there duplicate or conflicting inventory IDs across regions or business units?
- Are some screens mobile, temporary, or campaign-based?
- Does the company support sub-divisions or parent-child inventory units?

### Compliance and privacy questions

- Which fields are safe to expose publicly?
- Which contact fields are optional and likely omitted?
- Are there legal or privacy objections to publishing street address, city, or phone numbers?
- Are there any restrictions on hosting a public registry service?

### DNS and deployment questions

- Who controls the DNS zone and can publish TXT records?
- Are there separate production and staging domains?
- Can the registry host be a dedicated hostname under the media-owner domain?
- Is there any reverse-proxy, CDN, or backend path rewriting that could affect the public path structure?

---

## 11. Good implementation plan for an agent

A coding agent should work through the implementation in this order:

### Phase 1: Requirements and ownership

1. Confirm the authoritative domain and registry hostname.
2. Confirm which media-owner namespaces the registry covers.
3. Confirm whether multiple owners share one registry instance.
4. Identify the source-of-truth inventory system.

### Phase 2: Data inventory and schema mapping

1. Map each media owner to a reverse-DNS namespace.
2. Map internal IDs to canonical OOHDI identifiers.
3. Convert the public data model to OOHDI field names and nesting.
4. Identify which fields are optional and which are required.
5. Define lifecycle handling for replaced or removed inventory.

### Phase 3: HTTP API layer

1. Add the public registry endpoints.
2. Implement canonicalization and validation.
3. Return correct HTTP status codes.
4. Implement `421` logic for non-authoritative namespaces.
5. Ensure all read endpoints are public and unauthenticated.

### Phase 4: DNS and authority

1. Publish `_oohdi.<domain>` TXT records.
2. Confirm the hostname is correct and publicly resolvable.
3. Validate that the registry host serves the correct JSON over HTTPS.

### Phase 5: Acceptance testing

1. Validate a known media-owner record.
2. Validate a known inventory record.
3. Validate missing record handling.
4. Validate non-authoritative handling.
5. Validate reidentified and removed record handling.
6. Validate lowercase canonicalization.

---

## 12. Recommended acceptance checklist

The implementation is ready when all of the following are true:

- [ ] The registry is publicly reachable over HTTPS
- [ ] The DNS TXT record exists and declares exactly one authoritative registry
- [ ] The media-owner namespace is canonicalized correctly
- [ ] The media-owner endpoint returns valid public JSON
- [ ] The inventory-unit endpoint returns valid public JSON
- [ ] `200`, `301`, `304`, `404`, `410`, and `421` behaviors match expectations
- [ ] Canonical IDs are lowercase and properly namespaced
- [ ] JSON schemas match the OOHDI specification
- [ ] The service is read-only and does not require authentication
- [ ] Internal inventory data has been mapped without exposing sensitive internals
- [ ] Optional fields are correctly omitted when not present
- [ ] The implementation handles retired and replaced units correctly
- [ ] HTTP caching and rate limiting are in place

---

## 13. Risks and failure modes to watch for

The agent should actively guard against these common issues:

- using a full URL instead of bare hostname in the `r` DNS value
- allowing duplicate or conflicting authoritative registry declarations
- exposing internal IDs instead of canonical OOHDI identifiers
- failing to lowercase identifiers before comparison
- returning HTML or authentication-required pages instead of JSON
- accepting invalid characters in local display IDs
- mapping `fixed`/`mobile` semantics incorrectly
- using `404` for records that should be `410` or `301`
- treating a shared registry as authoritative for the wrong namespace
- publishing data that is not actually the source of truth for the owner namespace

---

## 14. References

Use these documents as the implementation baseline:

- [README.md](../README.md)
- [guides/registry-setup-guide.md](registry-setup-guide.md)
- [guides/registry-quickstart.md](registry-quickstart.md)
- [examples/fictional_registry](../examples/fictional_registry)

Additional technical references:

- RFC 3986 – URI Syntax: https://www.ietf.org/rfc/rfc3986.txt
- OpenOOH Venue Taxonomy: https://github.com/openooh/venue-taxonomy

---

## 15. Short prompt an agent can use with a developer

Use this prompt when working with a company that wants OOHDI support integrated into an existing platform:

> We need to implement an OOHDI-compatible registry on top of our existing platform. Please confirm the following: authoritative media-owner domain, public registry hostname, DNS ownership, namespace strategy, source-of-truth inventory records, existing screen identifiers, data privacy constraints, replacement/decommissioning behaviors, and whether the OOHDI registry is a public read-only API layer or a separate authoritative service. We need the public endpoints to follow the OOHDI contract, canonical identifiers, DNS authority semantics, and JSON payload requirements while preserving our existing platform data model.

---

## 16. Final guidance for the agent

The most important principle is that an OOHDI registry is not just “a JSON API.” It is a public, authoritative, DNS-backed registry for a specific media-owner namespace.

When integrating into an existing platform, the agent should focus on four things:

1. authority and DNS trust
2. canonical identifier generation
3. public read-only API behavior
4. stable mapping from internal records to the OOHDI model

If those are correct, the rest of the platform can usually be adapted around them without a disruptive rewrite.
