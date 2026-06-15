"""Tests for Hermes runtime config: env parsing, defaults, secret safety."""

from __future__ import annotations

from services.hermes.config import load_config


def _env(**overrides: str) -> dict[str, str]:
    base = {}
    base.update(overrides)
    return base


def test_disabled_by_default() -> None:
    config, provider = load_config(env={})
    assert config.enabled is False
    assert provider is None
    assert "disabled" in config.status_text()


def test_disabled_with_telegram_env_still_disabled() -> None:
    config, provider = load_config(
        env={
            "SAHAMLENS_TELEGRAM_BOT_TOKEN": "bot123",
            "SAHAMLENS_TELEGRAM_CHAT_ID": "chat456",
        }
    )
    assert config.enabled is False
    assert provider is None


def test_enabled_with_anthropic_no_key() -> None:
    config, provider = load_config(env={"SAHAMLENS_HERMES_ENABLED": "1"})
    assert config.enabled is True
    assert provider is not None
    assert config.provider_name == "anthropic"
    assert config.provider_configured is False
    assert config.telegram_configured is False


def test_enabled_with_anthropic_and_key() -> None:
    config, provider = load_config(
        env={
            "SAHAMLENS_HERMES_ENABLED": "1",
            "ANTHROPIC_API_KEY": "sk-ant-test",  # pragma: allowlist secret
        }
    )
    assert config.enabled is True
    assert provider is not None
    assert config.provider_name == "anthropic"
    assert config.provider_configured is True


def test_enabled_with_telegram_configured() -> None:
    config, _ = load_config(
        env={
            "SAHAMLENS_HERMES_ENABLED": "1",
            "SAHAMLENS_TELEGRAM_BOT_TOKEN": "bot123",
            "SAHAMLENS_TELEGRAM_CHAT_ID": "chat456",
        }
    )
    assert config.telegram_token_configured is True
    assert config.telegram_chat_id_configured is True
    assert config.telegram_configured is True
    assert "Telegram: configured" in config.status_text()


def test_enabled_with_openai_compatible() -> None:
    config, provider = load_config(
        env={
            "SAHAMLENS_HERMES_ENABLED": "1",
            "SAHAMLENS_LLM_PROVIDER": "openai_compatible",
            "SAHAMLENS_LLM_BASE_URL": "https://api.openai.com/v1",
            "SAHAMLENS_LLM_MODEL": "gpt-4",
            "SAHAMLENS_LLM_API_KEY": "sk-test",  # pragma: allowlist secret
        }
    )
    assert config.enabled is True
    assert provider is not None
    assert config.provider_name == "openai_compatible"
    assert config.provider_configured is True


def test_enabled_with_unknown_provider() -> None:
    config, provider = load_config(
        env={
            "SAHAMLENS_HERMES_ENABLED": "1",
            "SAHAMLENS_LLM_PROVIDER": "nonexistent_provider",
        }
    )
    assert config.enabled is True
    assert provider is None
    assert config.provider_configured is False


def test_enabled_true_alternate_truthy_values() -> None:
    for val in ("1", "true", "yes"):
        config, _ = load_config(env={"SAHAMLENS_HERMES_ENABLED": val})
        assert config.enabled is True, f"expected enabled for {val!r}"


def test_enabled_false_for_other_values() -> None:
    for val in ("0", "false", "no", "", "2"):
        config, _ = load_config(env={"SAHAMLENS_HERMES_ENABLED": val})
        assert config.enabled is False, f"expected disabled for {val!r}"


def test_secrets_not_in_status_text() -> None:
    config, _ = load_config(
        env={
            "SAHAMLENS_HERMES_ENABLED": "1",
            "ANTHROPIC_API_KEY": "sk-ant-supersecret",  # pragma: allowlist secret
            "SAHAMLENS_TELEGRAM_BOT_TOKEN": "bot-secret-token",
            "SAHAMLENS_TELEGRAM_CHAT_ID": "my-secret-chat",
        }
    )
    text = config.status_text()
    assert "sk-ant-supersecret" not in text
    assert "bot-secret-token" not in text
    assert "my-secret-chat" not in text


def test_session_id_present_when_enabled() -> None:
    config1, _ = load_config(env={"SAHAMLENS_HERMES_ENABLED": "1"})
    config2, _ = load_config(env={"SAHAMLENS_HERMES_ENABLED": "1"})
    assert len(config1.session_id) == 32
    assert config1.session_id != config2.session_id


def test_session_id_empty_when_disabled() -> None:
    config, _ = load_config(env={})
    assert config.session_id == ""


def test_config_fields_are_booleans() -> None:
    config, _ = load_config(env={"SAHAMLENS_HERMES_ENABLED": "1"})
    assert isinstance(config.enabled, bool)
    assert isinstance(config.telegram_token_configured, bool)
    assert isinstance(config.telegram_chat_id_configured, bool)
    assert isinstance(config.telegram_configured, bool)
    assert isinstance(config.provider_configured, bool)
