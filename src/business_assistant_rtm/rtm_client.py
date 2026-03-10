"""Thin wrapper around rtmilk.api_sync.API with lazy init and timeline caching."""

from __future__ import annotations

import logging

from rtmilk.api_sync import API
from rtmilk.models import (
    ListsResponse,
    NotesResponse,
    PriorityEnum,
    TagListResponse,
    TaskListResponse,
    TaskPayload,
    TaskResponse,
)

from .config import RtmSettings

logger = logging.getLogger(__name__)


class RtmClient:
    """Low-level RTM API client with lazy initialization and timeline caching."""

    def __init__(self, settings: RtmSettings) -> None:
        self._settings = settings
        self._api: API | None = None
        self._timeline: str | None = None

    def _get_api(self) -> API:
        """Lazy-init the RTM API client."""
        if self._api is None:
            self._api = API(
                self._settings.api_key,
                self._settings.shared_secret,
                self._settings.token,
            )
        return self._api

    def _get_timeline(self) -> str:
        """Create and cache a timeline for write operations."""
        if self._timeline is None:
            response = self._get_api().TimelinesCreate()
            self._timeline = response.timeline
        return self._timeline

    def get_lists(self) -> ListsResponse:
        """Get all RTM lists."""
        return self._get_api().ListsGetList()

    def get_tasks(
        self, filter_str: str | None = None, list_id: str | None = None
    ) -> TaskListResponse:
        """Get tasks with optional filter and list_id."""
        return self._get_api().TasksGetList(list_id=list_id, filter=filter_str)

    def get_tags(self) -> TagListResponse:
        """Get all tags."""
        return self._get_api().TagsGetList()

    def add_task(
        self, name: str, list_id: str | None = None, parse: bool = True
    ) -> TaskResponse:
        """Add a new task. With parse=True, supports Smart Add syntax."""
        return self._get_api().TasksAdd(
            timeline=self._get_timeline(),
            name=name,
            list_id=list_id,
            parse=parse,
        )

    def complete_task(
        self, list_id: str, taskseries_id: str, task_id: str
    ) -> TaskResponse:
        """Mark a task as complete."""
        return self._get_api().TasksComplete(
            timeline=self._get_timeline(),
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
        )

    def uncomplete_task(
        self, list_id: str, taskseries_id: str, task_id: str
    ) -> TaskResponse:
        """Mark a task as incomplete."""
        return self._get_api().TasksUncomplete(
            timeline=self._get_timeline(),
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
        )

    def delete_task(
        self, list_id: str, taskseries_id: str, task_id: str
    ) -> TaskResponse:
        """Delete a task."""
        return self._get_api().TasksDelete(
            timeline=self._get_timeline(),
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
        )

    def set_due_date(
        self, list_id: str, taskseries_id: str, task_id: str, due: str
    ) -> TaskResponse:
        """Set or change the due date (natural language supported)."""
        return self._get_api().TasksSetDueDate(
            timeline=self._get_timeline(),
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
            due=due,
            parse=True,
        )

    def set_priority(
        self, list_id: str, taskseries_id: str, task_id: str, priority: PriorityEnum
    ) -> TaskPayload:
        """Set the priority of a task."""
        return self._get_api().TasksSetPriority(
            timeline=self._get_timeline(),
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
            priority=priority,
        )

    def set_task_name(
        self, list_id: str, taskseries_id: str, task_id: str, name: str
    ) -> TaskResponse:
        """Rename a task."""
        return self._get_api().TasksSetName(
            timeline=self._get_timeline(),
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
            name=name,
        )

    def add_tags(
        self, list_id: str, taskseries_id: str, task_id: str, tags: list[str]
    ) -> TaskResponse:
        """Add tags to a task."""
        return self._get_api().TasksAddTags(
            timeline=self._get_timeline(),
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
            tags=tags,
        )

    def remove_tags(
        self, list_id: str, taskseries_id: str, task_id: str, tags: list[str]
    ) -> TaskResponse:
        """Remove tags from a task."""
        return self._get_api().TasksRemoveTags(
            timeline=self._get_timeline(),
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
            tags=tags,
        )

    def add_note(
        self, list_id: str, taskseries_id: str, task_id: str, title: str, text: str
    ) -> NotesResponse:
        """Add a note to a task."""
        return self._get_api().TasksNotesAdd(
            timeline=self._get_timeline(),
            list_id=list_id,
            taskseries_id=taskseries_id,
            task_id=task_id,
            note_title=title,
            note_text=text,
        )
