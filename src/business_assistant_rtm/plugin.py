"""Plugin registration — defines PydanticAI tools for RTM operations."""

from __future__ import annotations

import logging
from pathlib import Path

from business_assistant.agent.deps import Deps
from business_assistant.plugins.registry import PluginInfo, PluginRegistry
from pydantic_ai import RunContext, Tool
from rtmilk.authorization import AuthorizationSession

from .config import load_rtm_settings
from .constants import (
    PLUGIN_CATEGORY,
    PLUGIN_DATA_RTM_AUTH_SESSION,
    PLUGIN_DATA_RTM_SERVICE,
    PLUGIN_DATA_RTM_SETTINGS,
    PLUGIN_DESCRIPTION,
    PLUGIN_NAME,
    SYSTEM_PROMPT_RTM,
    SYSTEM_PROMPT_RTM_SETUP,
)
from .rtm_service import RtmService

logger = logging.getLogger(__name__)


def _get_service(ctx: RunContext[Deps]) -> RtmService:
    """Retrieve the RtmService from plugin_data."""
    return ctx.deps.plugin_data[PLUGIN_DATA_RTM_SERVICE]


# --- List / Search tools ---


def _rtm_list_lists(ctx: RunContext[Deps]) -> str:
    """List all RTM task lists (name, ID)."""
    return _get_service(ctx).list_lists()


def _rtm_list_tasks(ctx: RunContext[Deps], filter_str: str | None = None) -> str:
    """List tasks, optionally filtered with RTM filter syntax."""
    return _get_service(ctx).list_tasks(filter_str=filter_str)


def _rtm_search_tasks(ctx: RunContext[Deps], query: str) -> str:
    """Search tasks by keyword."""
    return _get_service(ctx).search_tasks(query)


def _rtm_list_tags(ctx: RunContext[Deps]) -> str:
    """List all tags in the RTM account."""
    return _get_service(ctx).list_tags()


# --- Task CRUD tools ---


def _rtm_add_task(
    ctx: RunContext[Deps], name: str, list_id: str | None = None
) -> str:
    """Add a task. Supports Smart Add syntax (e.g. "Buy milk tomorrow #shopping !1")."""
    return _get_service(ctx).add_task(name=name, list_id=list_id)


def _rtm_complete_task(
    ctx: RunContext[Deps], task_id: str, undo: bool = False
) -> str:
    """Mark a task as complete, or undo completion with undo=True."""
    service = _get_service(ctx)
    if undo:
        return service.uncomplete_task(task_id)
    return service.complete_task(task_id)


def _rtm_delete_task(ctx: RunContext[Deps], task_id: str) -> str:
    """Delete a task."""
    return _get_service(ctx).delete_task(task_id)


# --- Task Modification tools ---


def _rtm_update_task(
    ctx: RunContext[Deps],
    task_id: str,
    due: str = "",
    priority: str = "",
    name: str = "",
) -> str:
    """Update task fields. Only non-empty fields are updated."""
    service = _get_service(ctx)
    results: list[str] = []
    if due:
        results.append(service.set_due_date(task_id, due))
    if priority:
        results.append(service.set_priority(task_id, priority))
    if name:
        results.append(service.set_task_name(task_id, name))
    if not results:
        return "No fields to update — provide due, priority, or name."
    return "\n".join(results)


def _rtm_manage_tags(
    ctx: RunContext[Deps],
    task_id: str,
    tags: str,
    action: str = "add",
) -> str:
    """Manage task tags. action: add or remove."""
    service = _get_service(ctx)
    if action == "remove":
        return service.remove_tags(task_id, tags)
    return service.add_tags(task_id, tags)


def _rtm_add_note(
    ctx: RunContext[Deps], task_id: str, title: str, text: str
) -> str:
    """Add a note to a task."""
    return _get_service(ctx).add_note(task_id, title, text)


# --- Setup / Auth tools ---


def _rtm_start_auth(ctx: RunContext[Deps]) -> str:
    """Generate RTM authorization URL for the user to approve."""
    settings = ctx.deps.plugin_data[PLUGIN_DATA_RTM_SETTINGS]
    session = AuthorizationSession(
        settings.api_key, settings.shared_secret, "delete"
    )
    ctx.deps.plugin_data[PLUGIN_DATA_RTM_AUTH_SESSION] = session
    return (
        f"Open this URL to authorize RTM access:\n{session.url}\n\n"
        "After you click 'Allow' in your browser, tell me and "
        "I'll complete the setup."
    )


def _rtm_complete_auth(ctx: RunContext[Deps]) -> str:
    """Complete RTM authorization after user has approved access."""
    session = ctx.deps.plugin_data.get(PLUGIN_DATA_RTM_AUTH_SESSION)
    if session is None:
        return "No pending authorization. Please start the setup first."
    try:
        token = session.Done()
    except Exception as exc:
        return (
            f"Authorization failed: {exc}. "
            "Please try starting the auth again."
        )
    token_path = Path("data") / "rtm_token"
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(token, encoding="utf-8")
    del ctx.deps.plugin_data[PLUGIN_DATA_RTM_AUTH_SESSION]
    return (
        "RTM authorized! Token saved. "
        "Please fully stop and restart the bot to activate RTM tools."
    )


def register(registry: PluginRegistry) -> None:
    """Register the RTM plugin with the plugin registry.

    Reads RTM settings from environment. Skips registration
    if RTM_API_KEY is not configured.
    """
    settings = load_rtm_settings()
    if settings is None:
        logger.info(
            "RTM plugin: RTM_API_KEY not configured, skipping registration"
        )
        return

    if not settings.token:
        logger.info(
            "RTM plugin: RTM_TOKEN not configured, registering setup tools"
        )
        registry.plugin_data[PLUGIN_DATA_RTM_SETTINGS] = settings
        tools = [
            Tool(_rtm_start_auth, name="rtm_start_auth"),
            Tool(_rtm_complete_auth, name="rtm_complete_auth"),
        ]
        info = PluginInfo(
            name=PLUGIN_NAME,
            description=PLUGIN_DESCRIPTION,
            system_prompt_extra=SYSTEM_PROMPT_RTM_SETUP,
            category=PLUGIN_CATEGORY,
        )
        registry.register(info, tools)
        return

    service = RtmService(settings)

    tools = [
        Tool(_rtm_list_lists, name="rtm_list_lists"),
        Tool(_rtm_list_tasks, name="rtm_list_tasks"),
        Tool(_rtm_search_tasks, name="rtm_search_tasks"),
        Tool(_rtm_list_tags, name="rtm_list_tags"),
        Tool(_rtm_add_task, name="rtm_add_task"),
        Tool(_rtm_complete_task, name="rtm_complete_task"),
        Tool(_rtm_delete_task, name="rtm_delete_task"),
        Tool(_rtm_update_task, name="rtm_update_task"),
        Tool(_rtm_manage_tags, name="rtm_manage_tags"),
        Tool(_rtm_add_note, name="rtm_add_note"),
    ]

    info = PluginInfo(
        name=PLUGIN_NAME,
        description=PLUGIN_DESCRIPTION,
        system_prompt_extra=SYSTEM_PROMPT_RTM,
        category=PLUGIN_CATEGORY,
    )

    registry.register(info, tools)
    registry.plugin_data[PLUGIN_DATA_RTM_SERVICE] = service

    logger.info("RTM plugin registered with %d tools", len(tools))
