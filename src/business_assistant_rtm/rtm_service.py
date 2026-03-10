"""RtmService — wraps RtmClient for all RTM operations."""

from __future__ import annotations

import json
import logging

from rtmilk.models import PriorityEnum, Tags

from .config import RtmSettings
from .constants import (
    DEFAULT_TASK_FILTER,
    DEFAULT_TASK_LIMIT,
    PRIORITY_DISPLAY,
    PRIORITY_SORT_ORDER,
    TASK_ID_SEPARATOR,
)
from .rtm_client import RtmClient

logger = logging.getLogger(__name__)


class RtmService:
    """High-level RTM operations returning formatted strings for LLM consumption."""

    def __init__(self, settings: RtmSettings) -> None:
        self._settings = settings
        self._client = RtmClient(settings)

    @staticmethod
    def _parse_task_id(composite: str) -> tuple[str, str, str]:
        """Split a composite task ID into (list_id, taskseries_id, task_id)."""
        parts = composite.split(TASK_ID_SEPARATOR)
        if len(parts) != 3:
            msg = (
                f"Invalid task ID '{composite}'. "
                f"Expected format: list_id{TASK_ID_SEPARATOR}"
                f"taskseries_id{TASK_ID_SEPARATOR}task_id"
            )
            raise ValueError(msg)
        return parts[0], parts[1], parts[2]

    @staticmethod
    def _format_priority(priority: PriorityEnum) -> str:
        """Map PriorityEnum to human-readable display string."""
        return PRIORITY_DISPLAY.get(priority, "none")

    @staticmethod
    def _flatten_tasks(response) -> list[dict]:
        """Walk nested RTM task structure into flat dicts with composite _id."""
        tasks: list[dict] = []
        if response.tasks.list is None:
            return tasks

        for task_list in response.tasks.list:
            if task_list.taskseries is None:
                continue
            for ts in task_list.taskseries:
                for task in ts.task:
                    item: dict = {
                        "_id": (
                            f"{task_list.id}"
                            f"{TASK_ID_SEPARATOR}{ts.id}"
                            f"{TASK_ID_SEPARATOR}{task.id}"
                        ),
                        "name": ts.name,
                        "priority": PRIORITY_DISPLAY.get(
                            task.priority, "none"
                        ),
                    }
                    if task.due is not None:
                        item["due"] = task.due.isoformat()
                    if task.completed is not None:
                        item["completed"] = task.completed.isoformat()
                    # Extract tags
                    if isinstance(ts.tags, Tags) and ts.tags.tag:
                        item["tags"] = ts.tags.tag
                    tasks.append(item)
        return tasks

    @staticmethod
    def _sort_and_limit(tasks: list[dict]) -> list[dict]:
        """Sort tasks by priority (high first), then due date, and limit."""
        tasks.sort(
            key=lambda t: (
                PRIORITY_SORT_ORDER.get(t.get("priority", "none"), 3),
                t.get("due") or "9999-12-31",
            )
        )
        return tasks[:DEFAULT_TASK_LIMIT]

    def list_lists(self) -> str:
        """List all RTM task lists."""
        try:
            response = self._client.get_lists()
            items = []
            for rtm_list in response.lists.list:
                if rtm_list.deleted or rtm_list.archived:
                    continue
                items.append({
                    "_id": rtm_list.id,
                    "name": rtm_list.name,
                    "smart": rtm_list.smart,
                })
            return json.dumps({"lists": items})
        except Exception as e:
            return f"Error listing RTM lists: {e}"

    def list_tasks(self, filter_str: str | None = None) -> str:
        """List tasks with optional RTM filter.

        Defaults to incomplete tasks only, sorted by priority, max 100.
        """
        try:
            effective_filter = filter_str if filter_str is not None else DEFAULT_TASK_FILTER
            response = self._client.get_tasks(filter_str=effective_filter)
            tasks = self._flatten_tasks(response)
            if not tasks:
                return "No tasks found."
            tasks = self._sort_and_limit(tasks)
            return json.dumps({"tasks": tasks})
        except Exception as e:
            return f"Error listing tasks: {e}"

    def search_tasks(self, query: str) -> str:
        """Search tasks by keyword using RTM name filter.

        Only searches incomplete tasks, sorted by priority, max 100.
        """
        try:
            filter_str = f'{DEFAULT_TASK_FILTER} AND name:"{query}"'
            response = self._client.get_tasks(filter_str=filter_str)
            tasks = self._flatten_tasks(response)
            if not tasks:
                return f"No tasks matching '{query}' found."
            tasks = self._sort_and_limit(tasks)
            return json.dumps({"tasks": tasks})
        except Exception as e:
            return f"Error searching tasks: {e}"

    def list_tags(self) -> str:
        """List all tags in the account."""
        try:
            response = self._client.get_tags()
            tags = [tag.name for tag in response.tags.tag]
            return json.dumps({"tags": tags})
        except Exception as e:
            return f"Error listing tags: {e}"

    def add_task(self, name: str, list_id: str | None = None) -> str:
        """Add a new task using Smart Add syntax."""
        try:
            if list_id:
                smart_name = self._get_smart_list_name(list_id)
                if smart_name:
                    return (
                        f"Cannot add task to '{smart_name}' because it is a Smart List. "
                        "Please choose a regular list instead."
                    )
            response = self._client.add_task(name=name, list_id=list_id)
            ts = response.list.taskseries[0]
            return f"Task added: '{ts.name}'"
        except Exception as e:
            return f"Error adding task: {e}"

    def _get_smart_list_name(self, list_id: str) -> str | None:
        """Return the list name if list_id is a Smart List, else None."""
        try:
            response = self._client.get_lists()
            for rtm_list in response.lists.list:
                if rtm_list.id == list_id and rtm_list.smart:
                    return rtm_list.name
            return None
        except Exception:
            return None  # on error, allow the original call to proceed

    def complete_task(self, task_id: str) -> str:
        """Mark a task as complete."""
        try:
            list_id, ts_id, t_id = self._parse_task_id(task_id)
            self._client.complete_task(list_id, ts_id, t_id)
            return "Task marked as complete."
        except Exception as e:
            return f"Error completing task: {e}"

    def uncomplete_task(self, task_id: str) -> str:
        """Mark a task as incomplete."""
        try:
            list_id, ts_id, t_id = self._parse_task_id(task_id)
            self._client.uncomplete_task(list_id, ts_id, t_id)
            return "Task marked as incomplete."
        except Exception as e:
            return f"Error uncompleting task: {e}"

    def delete_task(self, task_id: str) -> str:
        """Delete a task."""
        try:
            list_id, ts_id, t_id = self._parse_task_id(task_id)
            self._client.delete_task(list_id, ts_id, t_id)
            return "Task deleted."
        except Exception as e:
            return f"Error deleting task: {e}"

    def set_due_date(self, task_id: str, due: str) -> str:
        """Set or change the due date of a task."""
        try:
            list_id, ts_id, t_id = self._parse_task_id(task_id)
            self._client.set_due_date(list_id, ts_id, t_id, due)
            return f"Due date set to '{due}'."
        except Exception as e:
            return f"Error setting due date: {e}"

    def set_priority(self, task_id: str, priority: str) -> str:
        """Set the priority of a task (1=high, 2=medium, 3=low, none)."""
        try:
            priority_map = {
                "1": PriorityEnum.Priority1,
                "2": PriorityEnum.Priority2,
                "3": PriorityEnum.Priority3,
                "none": PriorityEnum.NoPriority,
            }
            priority_enum = priority_map.get(priority.lower())
            if priority_enum is None:
                return f"Invalid priority '{priority}'. Use 1, 2, 3, or none."

            list_id, ts_id, t_id = self._parse_task_id(task_id)
            self._client.set_priority(list_id, ts_id, t_id, priority_enum)
            display = PRIORITY_DISPLAY[priority_enum]
            return f"Priority set to {display}."
        except Exception as e:
            return f"Error setting priority: {e}"

    def set_task_name(self, task_id: str, name: str) -> str:
        """Rename a task."""
        try:
            list_id, ts_id, t_id = self._parse_task_id(task_id)
            self._client.set_task_name(list_id, ts_id, t_id, name)
            return f"Task renamed to '{name}'."
        except Exception as e:
            return f"Error renaming task: {e}"

    def add_tags(self, task_id: str, tags: str) -> str:
        """Add tags to a task (comma-separated string)."""
        try:
            list_id, ts_id, t_id = self._parse_task_id(task_id)
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            self._client.add_tags(list_id, ts_id, t_id, tag_list)
            return f"Tags added: {', '.join(tag_list)}"
        except Exception as e:
            return f"Error adding tags: {e}"

    def remove_tags(self, task_id: str, tags: str) -> str:
        """Remove tags from a task (comma-separated string)."""
        try:
            list_id, ts_id, t_id = self._parse_task_id(task_id)
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            self._client.remove_tags(list_id, ts_id, t_id, tag_list)
            return f"Tags removed: {', '.join(tag_list)}"
        except Exception as e:
            return f"Error removing tags: {e}"

    def add_note(self, task_id: str, title: str, text: str) -> str:
        """Add a note to a task."""
        try:
            list_id, ts_id, t_id = self._parse_task_id(task_id)
            self._client.add_note(list_id, ts_id, t_id, title, text)
            return f"Note '{title}' added to task."
        except Exception as e:
            return f"Error adding note: {e}"
