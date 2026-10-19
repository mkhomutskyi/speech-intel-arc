"""Pure request helpers; no GPU imports or implicit downloads."""

import re
import secrets

MAX_AUDIO_BYTES = 25 * 1024 * 1024


def normalize_language(value):
    value = (value or "").strip().lower()
    if value and not re.fullmatch("[a-z]{2,3}", value):
        raise ValueError(
            "Use a two/three-letter language code or empty for automatic detection"
        )
    return value


def authorized(key, header):
    return not key or secrets.compare_digest(header, "Bearer " + key)
