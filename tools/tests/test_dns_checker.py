from oohdi_tools.dns_checker import discover_authoritative_registry


def test_dns_checker_handles_missing_records():
    result = discover_authoritative_registry("example.invalid")
    assert result["domain"] == "example.invalid"
    assert result["found"] is False
