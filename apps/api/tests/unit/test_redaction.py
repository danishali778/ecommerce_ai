from app.core.redaction import redact_text, redact_value


def test_redact_text_masks_token_like_strings():
    assert redact_text("token shpat_1234567890abcdef") == "token [REDACTED]"


def test_redact_value_masks_sensitive_keys_recursively():
    payload = {
        "access_token": "abc",
        "nested": {"client_secret": "def"},
        "safe": "value",
    }

    assert redact_value(payload) == {
        "access_token": "[REDACTED]",
        "nested": {"client_secret": "[REDACTED]"},
        "safe": "value",
    }
