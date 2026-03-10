"""Tests for RTM in-chat OAuth setup tools."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from business_assistant.agent.deps import Deps
from business_assistant.plugins.registry import PluginRegistry
from pydantic_ai import RunContext

from business_assistant_rtm.config import RtmSettings
from business_assistant_rtm.constants import (
    PLUGIN_DATA_RTM_AUTH_SESSION,
    PLUGIN_DATA_RTM_SETTINGS,
)
from business_assistant_rtm.plugin import (
    _rtm_complete_auth,
    _rtm_start_auth,
    register,
)


def _make_ctx(plugin_data: dict) -> RunContext[Deps]:
    """Create a minimal RunContext with the given plugin_data."""
    deps = MagicMock(spec=Deps)
    deps.plugin_data = plugin_data
    ctx = MagicMock(spec=RunContext)
    ctx.deps = deps
    return ctx


class TestStartAuth:
    @patch("business_assistant_rtm.plugin.AuthorizationSession")
    def test_generates_url_and_stores_session(
        self, mock_session_cls: MagicMock
    ) -> None:
        mock_session = mock_session_cls.return_value
        mock_session.url = "https://www.rememberthemilk.com/services/auth/?frob=abc"

        settings = RtmSettings(
            api_key="key", shared_secret="secret", token=""
        )
        plugin_data: dict = {PLUGIN_DATA_RTM_SETTINGS: settings}
        ctx = _make_ctx(plugin_data)

        result = _rtm_start_auth(ctx)

        mock_session_cls.assert_called_once_with("key", "secret", "delete")
        assert "https://www.rememberthemilk.com/services/auth/" in result
        assert plugin_data[PLUGIN_DATA_RTM_AUTH_SESSION] is mock_session


class TestCompleteAuth:
    def test_no_session_returns_error(self) -> None:
        plugin_data: dict = {}
        ctx = _make_ctx(plugin_data)

        result = _rtm_complete_auth(ctx)

        assert "No pending authorization" in result

    @patch("business_assistant_rtm.plugin.Path")
    def test_saves_token_and_cleans_session(
        self, mock_path_cls: MagicMock
    ) -> None:
        mock_session = MagicMock()
        mock_session.Done.return_value = "obtained_token_123"

        mock_token_path = MagicMock()
        mock_path_cls.return_value.__truediv__ = MagicMock(
            return_value=mock_token_path
        )

        plugin_data: dict = {PLUGIN_DATA_RTM_AUTH_SESSION: mock_session}
        ctx = _make_ctx(plugin_data)

        result = _rtm_complete_auth(ctx)

        mock_session.Done.assert_called_once()
        mock_token_path.parent.mkdir.assert_called_once_with(
            parents=True, exist_ok=True
        )
        mock_token_path.write_text.assert_called_once_with(
            "obtained_token_123", encoding="utf-8"
        )
        assert PLUGIN_DATA_RTM_AUTH_SESSION not in plugin_data
        assert "RTM authorized" in result

    def test_auth_failure_returns_error(self) -> None:
        mock_session = MagicMock()
        mock_session.Done.side_effect = RuntimeError("Invalid frob")

        plugin_data: dict = {PLUGIN_DATA_RTM_AUTH_SESSION: mock_session}
        ctx = _make_ctx(plugin_data)

        result = _rtm_complete_auth(ctx)

        assert "Authorization failed" in result
        assert "Invalid frob" in result


class TestSetupModeRegistration:
    @patch("business_assistant_rtm.plugin.AuthorizationSession")
    def test_registers_auth_tools_when_no_token(
        self, _mock_session_cls: MagicMock, monkeypatch
    ) -> None:
        monkeypatch.setenv("RTM_API_KEY", "test_key")
        monkeypatch.setenv("RTM_SHARED_SECRET", "test_secret")
        monkeypatch.delenv("RTM_TOKEN", raising=False)

        registry = PluginRegistry()
        register(registry)

        tools = registry.all_tools()
        assert len(tools) == 2
        tool_names = {t.name for t in tools}
        assert tool_names == {"rtm_start_auth", "rtm_complete_auth"}

    @patch("business_assistant_rtm.plugin.AuthorizationSession")
    def test_stores_settings_in_plugin_data(
        self, _mock_session_cls: MagicMock, monkeypatch
    ) -> None:
        monkeypatch.setenv("RTM_API_KEY", "test_key")
        monkeypatch.setenv("RTM_SHARED_SECRET", "test_secret")
        monkeypatch.delenv("RTM_TOKEN", raising=False)

        registry = PluginRegistry()
        register(registry)

        assert PLUGIN_DATA_RTM_SETTINGS in registry.plugin_data
        settings = registry.plugin_data[PLUGIN_DATA_RTM_SETTINGS]
        assert settings.api_key == "test_key"
        assert settings.shared_secret == "test_secret"
