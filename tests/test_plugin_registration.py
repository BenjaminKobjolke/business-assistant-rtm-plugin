"""Tests for plugin registration."""

from __future__ import annotations

from unittest.mock import patch

from business_assistant.plugins.registry import PluginRegistry

from business_assistant_rtm.constants import PLUGIN_DATA_RTM_SERVICE
from business_assistant_rtm.plugin import register


class TestPluginRegistration:
    def test_register_skips_without_config(self, monkeypatch) -> None:
        monkeypatch.delenv("RTM_API_KEY", raising=False)
        registry = PluginRegistry()
        register(registry)
        assert registry.all_tools() == []

    @patch("business_assistant_rtm.plugin.RtmService")
    def test_register_with_config(self, mock_service_cls, monkeypatch) -> None:
        monkeypatch.setenv("RTM_API_KEY", "test_key")
        monkeypatch.setenv("RTM_SHARED_SECRET", "test_secret")
        monkeypatch.setenv("RTM_TOKEN", "test_token")

        registry = PluginRegistry()
        register(registry)

        assert len(registry.all_tools()) == 10
        assert len(registry.plugins) == 1
        assert registry.plugins[0].name == "rtm"
        assert registry.system_prompt_extras() != ""

    @patch("business_assistant_rtm.plugin.RtmService")
    def test_register_stores_service_in_plugin_data(
        self, mock_service_cls, monkeypatch
    ) -> None:
        monkeypatch.setenv("RTM_API_KEY", "test_key")
        monkeypatch.setenv("RTM_SHARED_SECRET", "test_secret")
        monkeypatch.setenv("RTM_TOKEN", "test_token")

        registry = PluginRegistry()
        register(registry)

        assert PLUGIN_DATA_RTM_SERVICE in registry.plugin_data
        assert registry.plugin_data[PLUGIN_DATA_RTM_SERVICE] is mock_service_cls.return_value

    def test_register_without_token_registers_setup_tools(
        self, monkeypatch
    ) -> None:
        monkeypatch.setenv("RTM_API_KEY", "test_key")
        monkeypatch.setenv("RTM_SHARED_SECRET", "test_secret")
        monkeypatch.delenv("RTM_TOKEN", raising=False)

        registry = PluginRegistry()
        register(registry)

        assert len(registry.all_tools()) == 2
        assert len(registry.plugins) == 1
        assert registry.plugins[0].name == "rtm"
        assert "not yet authenticated" in registry.system_prompt_extras()
