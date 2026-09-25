import json

from oohdi_tools.schema_validator import validate_oohdi_record


def test_valid_record_passes():
    payload = {
        "identity": {
            "id": "com.foobaroutdoor/oohdi/abc-1234",
            "name": "Times Square Digital – Upper Panel",
        },
        "state": {
            "type": "digital",
            "status": "active",
        },
        "location": {
            "location_type": "fixed",
            "point": {"latitude": 40.712776, "longitude": -74.005974},
            "bounds": None,
        },
        "capabilities": {
            "media_formats": [
                {
                    "type": "digital_image",
                    "enabled": True,
                    "min_duration_seconds": 8,
                    "max_duration_seconds": 8,
                }
            ]
        },
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": "2025-06-01T12:00:00Z",
    }

    assert validate_oohdi_record(payload) == []


def test_invalid_record_reports_missing_fields():
    payload = {"identity": {"id": "com.foobaroutdoor/oohdi/abc-1234", "name": "Example"}}
    errors = validate_oohdi_record(payload)
    assert any("state is required" in err for err in errors)
