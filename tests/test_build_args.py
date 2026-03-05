"""Unit tests for _build_args timezone/locale injection and deprecation compat."""

import warnings

from cloakbrowser.browser import _build_args, _migrate_timezone_id


def test_timezone_injected():
    """--fingerprint-timezone flag should appear when timezone is set."""
    args = _build_args(stealth_args=True, extra_args=None, timezone="America/New_York")
    assert "--fingerprint-timezone=America/New_York" in args


def test_locale_injected():
    """--lang flag should appear when locale is set."""
    args = _build_args(stealth_args=True, extra_args=None, locale="en-US")
    assert "--lang=en-US" in args


def test_both_injected():
    """Both flags should appear when both are set."""
    args = _build_args(stealth_args=True, extra_args=None, timezone="Europe/Berlin", locale="de-DE")
    assert "--fingerprint-timezone=Europe/Berlin" in args
    assert "--lang=de-DE" in args


def test_timezone_independent_of_stealth_args():
    """--fingerprint-timezone should be injected even when stealth_args=False."""
    args = _build_args(stealth_args=False, extra_args=None, timezone="America/New_York", locale="en-US")
    assert "--fingerprint-timezone=America/New_York" in args
    assert "--lang=en-US" in args
    # No stealth fingerprint args
    assert not any(a.startswith("--fingerprint=") for a in args)


def test_no_flags_when_not_set():
    """No timezone/lang flags when params are None."""
    args = _build_args(stealth_args=True, extra_args=None)
    assert not any(a.startswith("--fingerprint-timezone=") for a in args)
    assert not any(a.startswith("--lang=") for a in args)


def test_extra_args_preserved():
    """Extra args should still be included alongside timezone/locale."""
    args = _build_args(stealth_args=True, extra_args=["--disable-gpu"], timezone="Asia/Tokyo", locale="ja-JP")
    assert "--disable-gpu" in args
    assert "--fingerprint-timezone=Asia/Tokyo" in args
    assert "--lang=ja-JP" in args


# --- _migrate_timezone_id deprecation compat ---


def test_migrate_old_param_only():
    """timezone_id in kwargs should be promoted to timezone."""
    kwargs = {"timezone_id": "Europe/Paris"}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = _migrate_timezone_id(None, kwargs)
    assert result == "Europe/Paris"
    assert "timezone_id" not in kwargs
    assert len(w) == 1 and issubclass(w[0].category, FutureWarning)


def test_migrate_new_param_wins():
    """Explicit timezone takes precedence; timezone_id is still popped."""
    kwargs = {"timezone_id": "Europe/Paris"}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = _migrate_timezone_id("UTC", kwargs)
    assert result == "UTC"
    assert "timezone_id" not in kwargs
    assert len(w) == 1


def test_migrate_no_old_param():
    """No warning when timezone_id is absent."""
    kwargs = {"other": "value"}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = _migrate_timezone_id("UTC", kwargs)
    assert result == "UTC"
    assert "other" in kwargs
    assert len(w) == 0


def test_migrate_both_none():
    """Neither param set — returns None, no warning."""
    kwargs = {}
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = _migrate_timezone_id(None, kwargs)
    assert result is None
    assert len(w) == 0


# --- Deduplication tests ---


def test_user_fingerprint_overrides_default():
    """User --fingerprint should override the random default seed."""
    args = _build_args(stealth_args=True, extra_args=["--fingerprint=99887"])
    fingerprint_args = [a for a in args if a.startswith("--fingerprint=")]
    assert len(fingerprint_args) == 1
    assert fingerprint_args[0] == "--fingerprint=99887"


def test_user_platform_overrides_default():
    """User --fingerprint-platform should override the default."""
    args = _build_args(stealth_args=True, extra_args=["--fingerprint-platform=linux"])
    platform_args = [a for a in args if a.startswith("--fingerprint-platform=")]
    assert len(platform_args) == 1
    assert platform_args[0] == "--fingerprint-platform=linux"


def test_timezone_param_overrides_user_arg():
    """Dedicated timezone param should override user arg."""
    args = _build_args(
        stealth_args=True,
        extra_args=["--fingerprint-timezone=Europe/London"],
        timezone="America/New_York",
    )
    tz_args = [a for a in args if a.startswith("--fingerprint-timezone=")]
    assert len(tz_args) == 1
    assert tz_args[0] == "--fingerprint-timezone=America/New_York"


def test_locale_param_overrides_user_arg():
    """Dedicated locale param should override user --lang arg."""
    args = _build_args(
        stealth_args=True,
        extra_args=["--lang=de-DE"],
        locale="en-US",
    )
    lang_args = [a for a in args if a.startswith("--lang=")]
    assert len(lang_args) == 1
    assert lang_args[0] == "--lang=en-US"


def test_no_duplicate_flags():
    """No flag key should appear more than once in the output."""
    args = _build_args(
        stealth_args=True,
        extra_args=["--fingerprint=99887", "--fingerprint-timezone=UTC", "--lang=fr-FR"],
        timezone="Europe/Berlin",
        locale="de-DE",
    )
    keys = [a.split("=", 1)[0] for a in args]
    assert len(keys) == len(set(keys)), f"Duplicate keys found: {keys}"


def test_non_value_flags_preserved():
    """Flags without = should be preserved without dedup issues."""
    args = _build_args(stealth_args=True, extra_args=["--disable-gpu", "--no-zygote"])
    assert "--disable-gpu" in args
    assert "--no-zygote" in args
    assert "--no-sandbox" in args


def test_override_logs_debug(caplog):
    """Should log debug message when an override happens."""
    import logging

    with caplog.at_level(logging.DEBUG, logger="cloakbrowser"):
        _build_args(stealth_args=True, extra_args=["--fingerprint=99887"])
    assert any("--fingerprint=" in r.message and "99887" in r.message for r in caplog.records)
