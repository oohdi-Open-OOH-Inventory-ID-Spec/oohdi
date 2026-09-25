# How to Set Up Your OOHDI Media Owner Records

This guide explains how a media owner can set up its public registry records, how to identify an authoritative registry, and how to make sure the company or CMS provider exposes the inventory in a standards-based way.

---

## 1. What a media owner needs to do

A media owner is the organization that owns or controls a screen inventory namespace. In OOHDI terms, the media owner is responsible for:

- owning or controlling the public DNS domain used for the namespace
- publishing an `_oohdi` TXT record that declares the authoritative registry
- ensuring that the chosen registry serves the correct public data
- keeping the registry metadata current
- making sure screen IDs and inventory records follow canonical naming rules

A media owner does not directly need to run a registry itself unless it chooses to operate its own authoritative service. In most cases, the media owner selects a registry provider and then points DNS to that provider.

---

## 2. Basic namespace and ownership model

The media owner owns a reverse-DNS namespace such as:

```text
com.foobaroutdoor
```

This becomes a public OOHDI namespace like:

```text
com.foobaroutdoor/oohdi
```

The media owner also owns a domain such as:

```text
foobaroutdoor.com
```

The authoritative registry must be declared under that domain using DNS.

---

## 3. Publish the registry declaration in DNS

The media owner must add a DNS TXT record at:

```text
_oohdi.foobaroutdoor.com
```

Example record:

```dns
TXT _oohdi.foobaroutdoor.com
v=OOHDI1; r=registry.foobaroutdoor.com;
```

### What this means

- `v=OOHDI1` indicates the OOHDI version
- `r=registry.foobaroutdoor.com` indicates the authoritative registry DNS name
- There should be only one declared registry at a time

### Important rules

- The value of `r` must be a hostname, not a full URL
- The registry must be served over HTTPS
- The registry should be public and read-only for OOHDI lookups

---

## 4. How to find a registry

A media owner can choose a registry in one of three common ways:

### Option 1: Use an external registry provider

The media owner signs a contract with a registry provider that manages the authoritative data service, DNS declaration, and public API.

### Option 2: Run the registry internally

The media owner operates the registry service itself and keeps the truth source internally.

### Option 3: Use a CMS or software partner

Some CMS providers or display software vendors offer an OOHDI-compatible registry service or can integrate with a registry provider.

### Discovery process

Clients discover the authoritative registry by querying DNS:

```text
TXT _oohdi.<media_owner_domain>
```

Then they read the `r=` value and look up the registry host.

Example flow:

1. Client checks `foobaroutdoor.com`
2. Client resolves `_oohdi.foobaroutdoor.com`
3. DNS returns `v=OOHDI1; r=registry.foobaroutdoor.com;`
4. Client calls:

```text
https://registry.foobaroutdoor.com/oohdi/com.foobaroutdoor
```

5. Registry returns the media owner record or a misdirected request if the namespace is wrong

---

## 5. Minimum registry data to publish

A media owner should ensure the registry exposes at least:

- a media-owner record for the organization itself
- one or more screen records
- correct canonical IDs
- valid timestamps
- correct status values

### Media owner record example

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

### Screen record example

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
    }
  },
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-06-15T10:00:00Z"
}
```

---

## 6. Recommended process for media owners

### Step 1: Confirm the namespace

Choose the media owner namespace and confirm that you control the domain.

Example:

```text
Media owner: Foobar Outdoor Media
Namespace: com.foobaroutdoor
Domain: foobaroutdoor.com
```

### Step 2: Select a registry provider

Choose a provider that can:

- host the authoritative service
- expose the required OOHDI endpoints
- support screen metadata publication
- maintain DNS declaration and API uptime

### Step 3: Publish the DNS TXT record

Add the TXT record:

```dns
TXT _oohdi.foobaroutdoor.com
v=OOHDI1; r=registry.foobaroutdoor.com;
```

### Step 4: Validate the registry endpoints

Test the public endpoints with curl or an API client:

```bash
curl -sS https://registry.foobaroutdoor.com/oohdi/com.foobaroutdoor
curl -sS https://registry.foobaroutdoor.com/oohdi/com.foobaroutdoor/oohdi/emp-001
```

### Step 5: Sync CMS or screen inventory data

Connect the CMS or screen inventory system to the registry data feed so every screen and location record has a canonical OOHDI identifier.

### Step 6: Maintain records

Update the registry when a screen is:

- added
- removed
- renamed
- moved
- decommissioned
- replaced

---

## 7. How to validate a registry before trusting it

Before moving a production namespace, test that the registry:

- returns the correct DNS record
- serves HTTPS only
- exposes the required endpoints
- returns `421` for non-authoritative namespaces
- returns proper `404` and `410` semantics
- conforms to stable JSON naming and canonical IDs

A simple validation flow is:

```bash
curl -I https://registry.foobaroutdoor.com/oohdi/com.foobaroutdoor
curl -sS https://registry.foobaroutdoor.com/oohdi/com.foobaroutdoor/oohdi/emp-001
```

---

## 8. Common mistakes to avoid

- Using a full URL in the DNS `r=` value instead of a hostname
- Publishing multiple registries for one namespace
- Serving HTTP instead of HTTPS
- Returning HTML instead of JSON
- Reusing screen IDs once they have been assigned
- Publishing missing or inconsistent timestamps

---

## 9. Summary

For a media owner, the main job is simple:

1. control the DNS namespace,
2. declare the authoritative registry using `_oohdi.<domain>`,
3. choose a registry provider or run one internally,
4. ensure records are published and kept current.

Once the DNS declaration and registry endpoints are working, the media owner can expose inventory in a way that buyers, ad-tech systems, and other partners can discover and validate reliably.

---

## 10. Quick checklist

- [ ] Own or control the media owner domain
- [ ] Select a registry provider or self-host the registry
- [ ] Publish `_oohdi.<domain>` TXT record
- [ ] Confirm registry host is the `r=` value
- [ ] Validate the public endpoints over HTTPS
- [ ] Publish the media owner and screen records
- [ ] Keep screen metadata current
- [ ] Test for bad namespace and missing record handling
