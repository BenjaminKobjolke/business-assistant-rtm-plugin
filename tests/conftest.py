"""Shared test fixtures for the RTM plugin."""

from __future__ import annotations

import pytest

from business_assistant_rtm.config import RtmSettings


@pytest.fixture()
def rtm_settings() -> RtmSettings:
    return RtmSettings(
        api_key="test_api_key",
        shared_secret="test_shared_secret",
        token="test_token",
    )
