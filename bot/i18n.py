"""
Internationalization (i18n) module.

Loads translation strings from JSON files in the locales/ directory.
To add a new language, create a new JSON file (e.g., locales/ru.json)
with the same keys as en.json and commit to the repository.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Directory containing locale JSON files
_LOCALES_DIR = Path(__file__).parent / "locales"

# In-memory cache: {"en": {"key": "value", ...}, "ru": {...}}
_translations: dict[str, dict[str, str]] = {}

# Default locale used when a key is missing in the requested locale
DEFAULT_LOCALE = "en"


def load_locales() -> None:
    """Load all available locale files into memory."""
    _translations.clear()
    if not _LOCALES_DIR.is_dir():
        logger.warning("Locales directory not found: %s", _LOCALES_DIR)
        return

    for path in sorted(_LOCALES_DIR.glob("*.json")):
        locale_code = path.stem  # e.g. "en", "ru"
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            _translations[locale_code] = data
            logger.info("Loaded locale '%s' (%d keys)", locale_code, len(data))
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load locale '%s': %s", locale_code, exc)

    if DEFAULT_LOCALE not in _translations:
        logger.error("Default locale '%s' is missing!", DEFAULT_LOCALE)


def get_available_locales() -> list[str]:
    """Return a sorted list of loaded locale codes."""
    return sorted(_translations.keys())


def t(key: str, locale: str = DEFAULT_LOCALE, **kwargs: object) -> str:
    """
    Get a translated string by key.

    Falls back to the default locale if the key is not found in the
    requested locale, and falls back to the raw key if not found at all.

    Supports Python str.format() placeholders:
        t("welcome", name="John") -> "Welcome, John!"
    """
    # Try requested locale first
    translations = _translations.get(locale, {})
    value = translations.get(key)

    # Fallback to default locale
    if value is None and locale != DEFAULT_LOCALE:
        value = _translations.get(DEFAULT_LOCALE, {}).get(key)

    # Fallback to raw key
    if value is None:
        logger.debug("Missing translation: key='%s', locale='%s'", key, locale)
        return key

    # Apply format substitutions
    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, IndexError) as exc:
            logger.warning(
                "Format error for key='%s', locale='%s': %s", key, locale, exc
            )

    return value
