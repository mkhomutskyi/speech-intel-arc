import pytest
from app.validation import normalize_language, authorized


@pytest.mark.parametrize("code", ["", "en", "ru", "uk"])
def test_language_codes_and_auto(code):
    assert normalize_language(code) == code


def test_no_silent_english_default():
    assert normalize_language(None) == ""
    assert normalize_language(" UK ") == "uk"


@pytest.mark.parametrize("code", ["english", "../en", "<|en|>"])
def test_rejects_invalid_language_fields(code):
    with pytest.raises(ValueError):
        normalize_language(code)


def test_bearer_auth():
    assert authorized("example", "Bearer example")
    assert not authorized("example", "Bearer other")
    assert not authorized("example", "")
    assert authorized("", "")
