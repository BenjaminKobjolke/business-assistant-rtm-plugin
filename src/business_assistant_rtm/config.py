"""Remember The Milk settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from .constants import ENV_RTM_API_KEY, ENV_RTM_SHARED_SECRET, ENV_RTM_TOKEN


@dataclass(frozen=True)
class RtmSettings:
    """RTM connection settings."""

    api_key: str
    shared_secret: str
    token: str


def load_rtm_settings() -> RtmSettings | None:
    """Load RTM settings from environment variables.

    Returns None if RTM_API_KEY is not configured.
    """
    api_key = os.environ.get(ENV_RTM_API_KEY, "")
    if not api_key:
        return None

    return RtmSettings(
        api_key=api_key,
        shared_secret=os.environ.get(ENV_RTM_SHARED_SECRET, ""),
        token=os.environ.get(ENV_RTM_TOKEN, ""),
    )
