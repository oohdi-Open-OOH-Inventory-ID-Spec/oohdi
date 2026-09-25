import argparse
import json
from datetime import datetime
from typing import Any, Dict, List


REQUIRED_TOP_LEVEL = {
    "identity",
    "state",
    "location",
    "capabilities",
    "created_at",
    "updated_at",
}

VALID_STATUS = {"planned", "active", "inactive", "maintenance", "decommissioned"}
VALID_STATE_TYPES = {"digital", "static", "print"}
VALID_MEDIA_FORMATS = {
    "digital_image",
    "digital_video",
    "static_poster",
    "static_vinyl",
}
VALID_LOCATION_TYPES = {"fixed", "mobile"}
VALID_VIEWER_CONTEXT = {"vehicular", "pedestrian", "queue", "seated"}
VALID_VIEWER_READS = {"L", "R", "C", "W", "omni"}
VALID_DIMENSION_UNITS = {"feet", "meters", "pixels"}


def _is_rfc3339(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError:
        return False


def validate_oohdi_record(record: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    if not isinstance(record, dict):
        return ["Record must be a JSON object."]

    missing = sorted(REQUIRED_TOP_LEVEL - set(record.keys()))
    if missing:
        errors.append(f"Missing required top-level fields: {', '.join(missing)}")

    identity = record.get("identity")
    if identity is None:
        errors.append("identity is required.")
    else:
        if not isinstance(identity, dict):
            errors.append("identity must be an object.")
        else:
            if "id" not in identity:
                errors.append("identity.id is required.")
            elif not isinstance(identity["id"], str):
                errors.append("identity.id must be a string.")
            if "name" not in identity:
                errors.append("identity.name is required.")
            elif not isinstance(identity["name"], str):
                errors.append("identity.name must be a string.")
            elif len(identity["name"]) > 255:
                errors.append("identity.name exceeds 255 characters.")
            if "description" in identity and len(str(identity["description"])) > 1000:
                errors.append("identity.description exceeds 1000 characters.")

    state = record.get("state")
    if state is None:
        errors.append("state is required.")
    else:
        if "type" not in state:
            errors.append("state.type is required.")
        elif state["type"] not in VALID_STATE_TYPES:
            errors.append("state.type must be one of: digital, static, print")
        if "status" not in state:
            errors.append("state.status is required.")
        elif state["status"] not in VALID_STATUS:
            errors.append("state.status must be one of the allowed enum values.")

    location = record.get("location")
    if location is None:
        errors.append("location is required.")
    else:
        if "location_type" not in location:
            errors.append("location.location_type is required.")
        elif location["location_type"] not in VALID_LOCATION_TYPES:
            errors.append("location.location_type must be fixed or mobile")

        point = location.get("point")
        bounds = location.get("bounds")
        if location.get("location_type") == "fixed":
            if point is None:
                errors.append("location.point is required for fixed displays.")
            if bounds is not None:
                errors.append("location.bounds must be null for fixed displays.")
        elif location.get("location_type") == "mobile":
            if bounds is None:
                errors.append("location.bounds is required for mobile displays.")

        if isinstance(point, dict):
            lat = point.get("latitude")
            lon = point.get("longitude")
            if lat is not None and (not isinstance(lat, (int, float)) or not (-90 <= lat <= 90)):
                errors.append("location.point.latitude must be a number between -90 and 90.")
            if lon is not None and (not isinstance(lon, (int, float)) or not (-180 <= lon <= 180)):
                errors.append("location.point.longitude must be a number between -180 and 180.")

    capabilities = record.get("capabilities")
    if capabilities is None:
        errors.append("capabilities is required.")
    else:
        formats = capabilities.get("media_formats")
        if not isinstance(formats, list) or len(formats) < 1:
            errors.append("capabilities.media_formats must be a non-empty array.")
        else:
            for idx, fmt in enumerate(formats):
                if not isinstance(fmt, dict):
                    errors.append(f"capabilities.media_formats[{idx}] must be an object.")
                    continue
                if "type" not in fmt:
                    errors.append(f"capabilities.media_formats[{idx}].type is required.")
                elif fmt["type"] not in VALID_MEDIA_FORMATS:
                    errors.append(f"capabilities.media_formats[{idx}].type is invalid.")
                if "enabled" not in fmt:
                    errors.append(f"capabilities.media_formats[{idx}].enabled is required.")
                else:
                    if not isinstance(fmt["enabled"], bool):
                        errors.append(f"capabilities.media_formats[{idx}].enabled must be boolean.")
                if fmt.get("type") in {"digital_image", "digital_video"}:
                    for field in ["min_duration_seconds", "max_duration_seconds"]:
                        if field not in fmt:
                            errors.append(f"capabilities.media_formats[{idx}].{field} is required for digital media formats.")
                    if "min_duration_seconds" in fmt and "max_duration_seconds" in fmt:
                        min_d = fmt["min_duration_seconds"]
                        max_d = fmt["max_duration_seconds"]
                        if not isinstance(min_d, int) or min_d <= 0:
                            errors.append(f"capabilities.media_formats[{idx}].min_duration_seconds must be a positive integer.")
                        if not isinstance(max_d, int) or max_d <= 0:
                            errors.append(f"capabilities.media_formats[{idx}].max_duration_seconds must be a positive integer.")
                        if isinstance(min_d, int) and isinstance(max_d, int) and max_d < min_d:
                            errors.append(f"capabilities.media_formats[{idx}].max_duration_seconds must be >= min_duration_seconds.")
                else:
                    if "min_duration_seconds" in fmt or "max_duration_seconds" in fmt:
                        errors.append(f"capabilities.media_formats[{idx}] duration fields must be omitted for static formats.")

    for key in ["created_at", "updated_at"]:
        value = record.get(key)
        if value is None:
            errors.append(f"{key} is required.")
        elif not isinstance(value, str) or not _is_rfc3339(value):
            errors.append(f"{key} must be an RFC3339 timestamp string.")

    device = record.get("device")
    if device is not None and isinstance(device, dict):
        if state is not None and state.get("type") == "digital":
            if "dimensions" not in device:
                errors.append("device.dimensions is required when device is present for digital state.")

    physical = record.get("physical")
    if physical is not None and isinstance(physical, dict):
        dims = physical.get("dimensions")
        if dims is not None:
            if "units" not in dims:
                errors.append("physical.dimensions.units is required when dimensions are present.")
            elif dims["units"] not in {"feet", "meters"}:
                errors.append("physical.dimensions.units must be feet or meters.")

    taxonomy = record.get("taxonomy")
    if taxonomy is not None and isinstance(taxonomy, dict):
        venue = taxonomy.get("venue_type_id")
        if venue is not None and not isinstance(venue, str):
            errors.append("taxonomy.venue_type_id must be a string when present.")

    extensions = record.get("extensions")
    if extensions is not None and not isinstance(extensions, dict):
        errors.append("extensions must be an object when present.")

    return errors


def validate_oohdi_file(file_path: str) -> List[str]:
    with open(file_path, "r", encoding="utf-8") as handle:
        record = json.load(handle)
    return validate_oohdi_record(record)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an OOHDI inventory record against core schema rules.")
    parser.add_argument("path", help="Path to a JSON record to validate")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        errors = validate_oohdi_file(args.path)
    except FileNotFoundError:
        print(f"File not found: {args.path}")
        return 2
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON: {exc}")
        return 2

    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
