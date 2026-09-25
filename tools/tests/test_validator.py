import json

import pytest

from oohdi_tools.validator import canonicalize_identifier, validate_identifier


def test_canonicalize_identifier_lowercases_and_keeps_namespace():
    assert canonicalize_identifier("com.foobaroutdoor/oohdi/ABC-1234") == "com.foobaroutdoor/oohdi/abc-1234"


def test_canonicalize_identifier_rejects_bad_format():
    with pytest.raises(ValueError):
        canonicalize_identifier("bad-id")


def test_validate_identifier_reports_errors():
    assert validate_identifier("bad-id")
