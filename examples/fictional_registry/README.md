# Fictional OOHDI Registry Example

This example provides a fully self-contained, fictional OOHDI registry service for local learning and testing.

## Scope

- Fictional media owner domain: `example-media-owner.oohdi.org`
- Fictional registry host: `example-registry.oohdi.org`
- Registry namespace: `org.oohdi.example-media-owner`
- 20 sample sellable inventory records

## Local run

```bash
docker compose up --build
```

The service will be available at:

- http://localhost:18080/
- http://localhost:18080/oohdi/org.oohdi.example-media-owner
- http://localhost:18080/oohdi/org.oohdi.example-media-owner/emp-001

## DNS discovery example

The fictional media owner would publish a DNS TXT record like:

```text
_oohdi.example-media-owner.oohdi.org. TXT "v=OOHDI1; r=example-registry.oohdi.org;"
```

## Example canonical IDs

```text
org.oohdi.example-media-owner/oohdi/emp-001
org.oohdi.example-media-owner/oohdi/emp-020
```

## Notes

This registry is intentionally fictional and is designed for examples, demos, and local validation workflows.
