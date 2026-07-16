# oohdi: Out Of Home Display Identifier Specification

Version: 0.1

## 1. Introduction

### Purpose

The purpose of the `oohdi` (`Oooh-Dee`) specification is to establish a globally unique, decentralized identifier for Out-of-Home (OOH) sellable inventory units, facilitating discovery, identification, verification, and data interoperability across the OOH ecosystem.

### Audience

This specification targets media owners, registries, SSPs, DSPs, advertising agencies, and ad-tech industry technology providers.

#### Media Owners

Ensure that your displays can be found by any buyer

#### Agencies and Media Buyers

Verify that the displays that you are buying exist, are active and are in places you want to buy

#### Creative Teams

Validate that the ad creatives you are building, match the size specifications for the displays you are designing for.

#### Content Management Systems (CMS)

Create a common way to represent, publish and promote display inventory for your users

#### DSP's

De-duplicate and validate display inventory across all SSP's

#### SSP's

Verify that ever changing media owner inventory is active, up to date, and accurately described

#### Ad Tech Providers

Innovate and build tools that interact with display data

---

## 2. Problem Statement

Millions of OOH displays globally run content and advertisements, managed by numerous entities (SSPs, DSPs, Media Owners). The lack of a unified, standardized identifier creates:

* Difficulty in globally identifying sellable inventory units
* Challenges in locating accurate display information
* Issues verifying display existence and status
* Complexities in deduplicating inventory across datasets
* Increased fragmentation, inefficiency, and cost

---

## 3. Objectives and Requirements

* **Decentralization:** Registry data ownership remains distributed and open (similar to DNS)
* **Global Uniqueness:** Identifiers must avoid collisions across media owners
* **Scoping:** Identifiers must clearly encode ownership
* **Public Discoverability:** Identifiers must resolve to standardized, publicly accessible data
* **Privacy and Security:** Clear delineation of public versus sensitive data
* **Backward Compatibility:** Newer registry versions must support older clients
* **Extensibility:** Vendor-specific data must not break interoperability

---

## 4. Design Principles

The `oohdi` specification is guided by the following principles:

* **Decentralized Authority:** No central registry or governing body is required
* **DNS-Based Trust:** Control of a domain implies authority over identifiers scoped under that domain
* **Stable Identifiers, Mutable Metadata:** Identifiers are stable; metadata may evolve
* **Sellable Inventory Focus:** Identifiers represent sellable inventory units, not campaigns or creatives
* **Public by Default:** Core registry data is publicly readable
* **Backward Compatibility First:** Older clients must continue to function
* **Minimal Required Fields:** Encourage adoption through simplicity
* **Extensible Without Fragmentation:** Extensions must not override core semantics

---

## 5. Identifier Specification

### Identifier Structure

All `oohdi` identifiers use the following format:

```
<REVERSE_DNS_NAME>/oohdi/<MEDIA_OWNER_DISPLAY_ID>
```

**Components:**

* **`<REVERSE_DNS_NAME>`**
  The Media Owner’s primary DNS domain in reverse order (e.g. `com.foobaroutdoor`)

* **`/oohdi/`**
  Fixed namespace segment indicating the `oohdi` identifier scheme

* **`<MEDIA_OWNER_DISPLAY_ID>`**
  Media Owner-defined identifier, unique within the organization

**Examples:**

```
com.foobaroutdoor/oohdi/ab-1234-c
uk.co.barfoodmedia/oohdi/98765
```

---

### Allowed Characters

The `<MEDIA_OWNER_DISPLAY_ID>` MUST conform to RFC 3986 unreserved characters:

* `A–Z`, `a–z`, `0–9`, `-`, `.`, `_`, `~`

---

### Case Sensitivity and Canonical Form

All `oohdi` identifiers are **case-insensitive**.

**Canonical Form Rules:**

* Identifiers MUST be normalized to lowercase
* Identifiers MUST NOT include a trailing slash
* Percent-encoding MUST NOT be used for unreserved characters
* Clients MUST normalize identifiers before comparison or storage
* Registries MUST return identifiers in canonical form

**Canonical Example:**

```
com.foobaroutdoor/oohdi/abc-1234
```

---

### Identifier Length Limits

**Total Identifier Length:**
- MUST NOT exceed 255 characters

## 6. Registry Discovery

Media Owners MUST publish a DNS `TXT` record declaring their Authoritative Registry.

```
_oohdi.<media_owner_domain>
```

**Example:**

```
TXT _oohdi.foobaroutdoor.com
```

**Example Response:**

```
v=OOHDI1; r=registry.example.com;
```

### Fields

* `v` – Supported `oohdi` major version
* `r` – DNS name of the Authoritative Registry

### r Format

* correct : v=OOHDI1; r=registry.example.com;
* incorrect : v=OOHDI1; r=https://registry.example.com;

### Recommended TTL

3600 seconds

### Source of Truth

Only a single registry is supported as the source of truth for any media owner domain

### Discovery Scope

This specification defines only two public, unauthenticated read endpoints:

* Media Owner Information
* Sellable Inventory Unit Information

These endpoints are intended for identifier validation, metadata verification, and per-identifier synchronization.

Enumeration or bulk discovery of all inventory for a media owner is out of scope for this specification.
Registries MAY provide additional discovery mechanisms (for example: list endpoints, feeds, or files), but clients MUST NOT assume they exist.

---

### Version Compatibility

* Registries advertising newer versions (e.g. `OOHDI2`) MUST remain backward compatible
* Clients written for `OOHDI1` MUST function correctly against newer registries
* Registries MAY add fields but MUST NOT remove or redefine existing fields

---

## 7. Registry Architecture

### Definitions

**Registry Provider**
An organization that provides screen registry services. A Registry Provider may host registries for one or more Media Owners.

**Registry**
The HTTP-based service that exposes authoritative metadata for `oohdi` identifiers.

**Authoritative Registry**
The Registry designated by a Media Owner via DNS as the authoritative source of truth for their identifiers.

### Authority and Ownership Rules

* A Media Owner is authoritative for identifiers scoped under its reverse-DNS namespace when it controls the corresponding forward DNS domain.
* Authority is established through the `_oohdi.<media_owner_domain>` TXT record.
* The TXT record MUST declare exactly one authoritative registry (`r`) for that domain at a time.
* Clients MUST treat the registry declared in current DNS as authoritative.
* When a Media Owner changes registries, it MUST update DNS; clients MUST follow DNS after propagation.
* Sub-brands or delegated business units SHOULD use delegated domains and corresponding reverse-DNS namespaces, each with their own `_oohdi` TXT record.

---

## 8. Registry API

Registries MUST:

* Serve content exclusively over HTTPS
* Be publicly readable without authentication
* Implement reasonable rate limiting
* Follow HTTP caching best practices

All required fields defined by this specification are public.

---

### API Endpoints

### Non-Authoritative Namespace Handling

If a registry receives a request for a `<REVERSE_DNS_NAME>` it is not authoritative for, it MUST return:

* `421 Misdirected Request`
* `error_code` = `not_authoritative`

Registries MAY include an advisory hint to the authoritative registry when known from DNS discovery.

If no `_oohdi.<media_owner_domain>` TXT record exists (or no usable `r` value can be derived), the registry MUST still return `421 Misdirected Request` with `error_code = not_authoritative`, and MUST omit the authoritative registry hint.

For non-authoritative namespaces, registries MUST NOT return lifecycle or existence statuses (`200`, `301`, `304`, `404`, `410`).

Recommended error payload:

```json
{
  "error_code": "not_authoritative",
  "message": "This registry is not authoritative for the requested media owner namespace.",
  "authoritative_registry_hint": "registry.example.com"
}
```

When no authoritative registry can be discovered via DNS, omit `authoritative_registry_hint`.

#### Media Owner Information

**Endpoint:**

```
GET https://<DISPLAY_REGISTRY_DNS_NAME>/oohdi/<REVERSE_DNS_NAME>
```

**Responses:**

* `200 OK` – Organization data
* `301 Moved Permanently` – Organization renamed or acquired
* `304 Not Modified` – No change
* `421 Misdirected Request` – Registry is not authoritative for the requested namespace
* `404 Not Found` – Organization never existed
* `410 Gone` – Organization no longer exists

**Schema:**

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `id` | String | Yes | The canonical oohdi organization identifier | Must match `<REVERSE_DNS_NAME>/oohdi` |
| `organization` | String | Yes | Legal or trading name of the Media Owner | Max 255 characters |
| `street_address` | String | No | Street address of primary business location | Max 255 characters |
| `city` | String | No | City of primary business location | Max 100 characters |
| `region` | String | No | State, province, or region code | Max 100 characters |
| `country` | String | No | ISO 3166-1 alpha-2 country code | 2 characters (e.g., `US`, `GB`, `CA`) |
| `phone_number` | String | No | Primary contact phone number | E.164 format recommended |
| `email_address` | String | No | Primary contact email address | Valid email format |
| `website` | String | Yes | Organization website URL | Valid HTTPS URL |
| `created_at` | String | Yes | ISO 8601 timestamp of organization record creation | RFC 3339 format |
| `updated_at` | String | Yes | ISO 8601 timestamp of last update | RFC 3339 format |

**Example Response:**

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

---

#### Sellable Inventory Unit Information

**Endpoint:**

```
GET https://<DISPLAY_REGISTRY_DNS_NAME>/oohdi/<REVERSE_DNS_NAME>/<MEDIA_OWNER_DISPLAY_ID>
```

**Responses:**

* `200 OK` – Inventory unit data
* `301 Moved Permanently` – Unit re-identified, replaced, or acquired by a new Media Owner
  (Location header MUST point to the new canonical identifier)
* `304 Not Modified` – No change
* `421 Misdirected Request` – Registry is not authoritative for the requested namespace
* `404 Not Found` – Unit never existed
* `410 Gone` – Unit permanently removed with no replacement

### Identifier Lifecycle and Persistence

* Once issued, an `oohdi` identifier MUST NOT be reassigned to a different sellable inventory unit.
* If a unit is replaced or re-identified, registries SHOULD return `301 Moved Permanently` from the old identifier to the successor identifier.
* If a unit is permanently removed with no successor, registries SHOULD return `410 Gone`.
* `404 Not Found` indicates the unit did not exist in the authoritative registry context.
* Retention duration for historical identifiers is implementation-defined.

---

**Schema:**

#### Identity Fields

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `identity` | Object | Yes | Identifier and descriptive information | |
| `identity.id` | String | Yes | The canonical oohdi identifier | Must match URL path; lowercase |
| `identity.name` | String | Yes | Human-readable display name | Max 255 characters |
| `identity.description` | String | No | Extended description of the unit | Max 1000 characters |

#### State Fields

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| `state` | Object | Yes | Current operational state | |
| `state.type` | Enum | Yes | Display technology type | `digital`, `static`, `print` |
| `state.status` | Enum | Yes | Current operational status | `planned`, `active`, `inactive`, `maintenance`, `decommissioned` |

#### Inventory Fields

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `inventory` | Object | No | Inventory hierarchy information | |
| `inventory.unit_type` | Enum | No | Type of sellable unit | `display`, `segment`, `structure` |
| `inventory.parent_unit_id` | String | No | Parent unit if this is a subdivision | Must be valid oohdi identifier |

Hierarchy Rules:

* Hierarchies MAY contain multiple levels.
* `parent_unit_id` MAY reference identifiers in the same or a different media owner namespace.
* Circular references are forbidden.
* Registries MUST reject records that introduce direct or indirect cycles.

#### Location Fields

| Field | Type | Required | Description | Valid Values / Constraints |
|-------|------|----------|-------------|---------------------------|
| `location` | Object | Yes | Geographic location information | |
| `location.location_type` | Enum | Yes | Location permanence type | `fixed`, `mobile` |
| `location.point` | Object | Conditional | Geographic coordinates | Required for `fixed`; represents center for `mobile` |
| `location.point.latitude` | Number | Conditional | Latitude in decimal degrees | -90 to 90 |
| `location.point.longitude` | Number | Conditional | Longitude in decimal degrees | -180 to 180 |
| `location.bounds` | Object | Conditional | Operating area boundary | Required for `mobile`; must be null for `fixed` |
| `location.bounds.type` | String | Conditional | GeoJSON geometry type | `Polygon` |
| `location.bounds.coordinates` | Array | Conditional | GeoJSON coordinate array | Standard GeoJSON format |

#### Physical Fields

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `physical` | Object | No | Physical characteristics | |
| `physical.dimensions` | Object | No | Dimensional specifications | |
| `physical.dimensions.units` | Enum | Conditional | Unit of measurement | `feet`, `meters`; required if dimensions provided |
| `physical.dimensions.width` | Number | No | Display width | Positive number |
| `physical.dimensions.height` | Number | No | Display height | Positive number |
| `physical.dimensions.elevation` | Number | No | Height above ground level | Positive number |
| `physical.facing` | Number | No | Compass bearing in degrees | 0-359 (0=North, 90=East, 180=South, 270=West) |
| `physical.viewer` | Object | No | Viewer characteristics and orientation | |
| `physical.viewer.context` | Enum | No | Viewer context or environment type | `vehicular`, `pedestrian`, `queue`, `seated` |
| `physical.viewer.reads` | Enum | No | Traffic direction relative to display | `L` (left), `R` (right), `C` (center), `W` (wall), `omni` (omnidirectional) |

#### Device Fields

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `device` | Object | Conditional | Device metadata for digital inventory units | Required when `state.type` is `digital` |
| `device.dimensions` | Object | Yes (if `device` provided) | Display device pixel dimensions | |
| `device.dimensions.units` | Enum | Yes (if `device` provided) | Unit of measurement | `pixels` |
| `device.dimensions.width` | Number | Yes (if `device` provided) | Device pixel width | Positive integer |
| `device.dimensions.height` | Number | Yes (if `device` provided) | Device pixel height | Positive integer |
| `device.player` | Object | No | Playback platform metadata | |
| `device.player.platform` | String | No | Name of the player platform | Max 255 characters |
| `device.player.version` | String | No | Player platform version | Max 100 characters |

#### Capabilities Fields

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `capabilities` | Object | Yes | Display capabilities and specifications | |
| `capabilities.media_formats` | Array | Yes | Supported media format specifications | Minimum 1 format |
| `capabilities.media_formats[].type` | Enum | Yes | Media format type | `digital_image`, `digital_video`, `static_poster`, `static_vinyl` |
| `capabilities.media_formats[].enabled` | Boolean | Yes | Whether format is currently available | `true` or `false` |
| `capabilities.media_formats[].min_duration_seconds` | Number | Conditional | Minimum display duration in seconds | Required for digital formats; positive integer |
| `capabilities.media_formats[].max_duration_seconds` | Number | Conditional | Maximum display duration in seconds | Required for digital formats; positive integer; >= min_duration_seconds |

Validation Rules:

* Duration fields MUST be omitted for static formats.
* Duration fields are required for digital formats.

#### Taxonomy Fields

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `taxonomy` | Object | No | Classification and categorization | |
| `taxonomy.venue_type_id` | String | No | OpenOOH venue taxonomy identifier | Format: `openooh:venue:<code>` |

#### Metadata Fields

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `extensions` | Object | No | Vendor-specific extensions | Must be namespaced; cannot override core fields |
| `created_at` | String | Yes | ISO 8601 timestamp of record creation | RFC 3339 format |
| `updated_at` | String | Yes | ISO 8601 timestamp of last update | RFC 3339 format |

---

### Example Response

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
    "bounds": null
  },
  "physical": {
    "dimensions": {
      "units": "feet",
      "width": 48,
      "height": 14,
      "elevation": 25.0
    },
    "facing": 90,
    "viewer": {
      "context": "vehicular",
      "reads": "R"
    }
  },
  "device": {
    "dimensions": {
      "units": "pixels",
      "width": 1400,
      "height": 400
    },
    "player": {
      "platform": "MyPlayerPlatform",
      "version": "8.4.12"
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
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-06-01T12:00:00Z"
}
```

---

## 9. Location Semantics

* `fixed` – Permanently installed at a single location

  * `bounds` MUST be null
* `mobile` – Moves within a defined geographic area

  * `bounds` MUST be defined and represent maximum operating area

Identifier semantics for mobile units:

* The identifier represents the sellable inventory unit, not a fixed point.
* `location.point` represents the current or representative center point.
* `location.bounds` represents the operating area envelope.
* Buying and transaction logic is out of scope.

---

## 10. Privacy and Security Considerations

* Registries MUST be read-only for public access
* No personally identifiable information is required
* Contact information is OPTIONAL
* Authentication and write operations are out of scope
* All required fields in this specification are public
* Optional fields MAY be omitted by the registry operator

---

## 11. Extensibility

The `extensions` object allows vendor-specific data.

**Rules:**

* Extensions MUST be namespaced
* Extensions MUST NOT redefine or override core fields
* Clients MUST ignore unknown extensions

Recommended namespacing format: `<namespace>/<field>` or `<namespace>:<field>`.

---

## 12. Identifier Semantics

An `oohdi` identifier represents a **sellable inventory unit**.

A sellable unit MAY represent:

* An entire physical display
* A subdivided region of a display
* Any independently sellable portion of a physical structure

Sellable units MAY reference a parent unit using `parent_unit_id`, which MUST itself be a valid `oohdi` identifier.

---

## 13. Definitions and Terminology

* **OOH:** Out-Of-Home advertising
* **Media Owner:** Organization owning the physical structure
* **Sellable Inventory Unit:** A unit of inventory that can be independently transacted
* **Registry Provider:** Organization providing registry services
* **Registry:** HTTP service exposing authoritative data
* **Authoritative Registry:** Registry designated via DNS
* **`<REVERSE_DNS_NAME>`:** Reverse DNS name of the Media Owner
* **`<MEDIA_OWNER_DISPLAY_ID>`:** Media Owner-assigned local identifier

---

## 14. References

* RFC 3986 – URI Syntax
  [https://www.ietf.org/rfc/rfc3986.txt](https://www.ietf.org/rfc/rfc3986.txt)
* OpenOOH Venue Taxonomy
  [https://github.com/openooh/venue-taxonomy](https://github.com/openooh/venue-taxonomy)
