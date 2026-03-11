"""Tests for RtmService with mocked RtmClient."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from rtmilk.models import PriorityEnum, Tags

from business_assistant_rtm.config import RtmSettings
from business_assistant_rtm.rtm_service import RtmService


def _make_task(
    task_id: str = "t1",
    due=None,
    completed=None,
    priority: PriorityEnum = PriorityEnum.NoPriority,
) -> MagicMock:
    """Create a mock Task object."""
    task = MagicMock()
    task.id = task_id
    task.due = due
    task.completed = completed
    task.priority = priority
    return task


def _make_taskseries(
    ts_id: str = "ts1",
    name: str = "Test Task",
    tags: list[str] | None = None,
    tasks: list | None = None,
) -> MagicMock:
    """Create a mock TaskSeries object."""
    ts = MagicMock()
    ts.id = ts_id
    ts.name = name
    if tags:
        ts.tags = Tags(tag=tags)
    else:
        ts.tags = []
    ts.task = tasks if tasks else [_make_task()]
    return ts


def _make_task_list(
    list_id: str = "L1",
    taskseries: list | None = None,
    has_taskseries: bool = True,
) -> MagicMock:
    """Create a mock TasksInListPayload object."""
    tl = MagicMock()
    tl.id = list_id
    if not has_taskseries:
        tl.taskseries = None
    else:
        tl.taskseries = taskseries if taskseries else [_make_taskseries()]
    return tl


def _make_task_list_response(task_lists: list | None = None) -> MagicMock:
    """Create a mock TaskListResponse."""
    response = MagicMock()
    response.tasks.list = task_lists
    return response


class TestRtmService:
    def _make_service(
        self, settings: RtmSettings, mock_client: MagicMock
    ) -> RtmService:
        """Create a service with a pre-injected mock client."""
        service = RtmService(settings)
        service._client = mock_client
        return service

    def test_parse_task_id_valid(self) -> None:
        list_id, ts_id, t_id = RtmService._parse_task_id("100/200/300")
        assert list_id == "100"
        assert ts_id == "200"
        assert t_id == "300"

    def test_parse_task_id_invalid(self) -> None:
        with pytest.raises(ValueError, match="Invalid task ID"):
            RtmService._parse_task_id("invalid")

    def test_parse_task_id_too_many_parts(self) -> None:
        with pytest.raises(ValueError, match="Invalid task ID"):
            RtmService._parse_task_id("1/2/3/4")

    def test_format_priority(self) -> None:
        assert RtmService._format_priority(PriorityEnum.Priority1) == "high"
        assert RtmService._format_priority(PriorityEnum.Priority2) == "medium"
        assert RtmService._format_priority(PriorityEnum.Priority3) == "low"
        assert RtmService._format_priority(PriorityEnum.NoPriority) == "none"

    def test_flatten_tasks_empty(self) -> None:
        response = _make_task_list_response(task_lists=None)
        assert RtmService._flatten_tasks(response) == []

    def test_flatten_tasks_with_data(self) -> None:
        task = _make_task(task_id="t1", priority=PriorityEnum.Priority1)
        ts = _make_taskseries(ts_id="ts1", name="Buy milk", tags=["shopping"], tasks=[task])
        tl = _make_task_list(list_id="L1", taskseries=[ts])
        response = _make_task_list_response(task_lists=[tl])

        tasks = RtmService._flatten_tasks(response)

        assert len(tasks) == 1
        assert tasks[0]["_id"] == "L1/ts1/t1"
        assert tasks[0]["name"] == "Buy milk"
        assert tasks[0]["priority"] == "high"
        assert tasks[0]["tags"] == ["shopping"]

    def test_flatten_tasks_no_taskseries(self) -> None:
        tl = _make_task_list(list_id="L1", has_taskseries=False)
        response = _make_task_list_response(task_lists=[tl])

        tasks = RtmService._flatten_tasks(response)
        assert tasks == []

    def test_list_lists(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        rtm_list1 = MagicMock()
        rtm_list1.id = "1"
        rtm_list1.name = "Inbox"
        rtm_list1.deleted = False
        rtm_list1.archived = False
        rtm_list1.smart = False

        rtm_list2 = MagicMock()
        rtm_list2.id = "2"
        rtm_list2.name = "Archived"
        rtm_list2.deleted = False
        rtm_list2.archived = True
        rtm_list2.smart = False

        mock_client.get_lists.return_value.lists.list = [rtm_list1, rtm_list2]
        service = self._make_service(rtm_settings, mock_client)

        result = service.list_lists()
        data = json.loads(result)

        assert len(data["lists"]) == 1
        assert data["lists"][0]["name"] == "Inbox"

    def test_list_tasks_with_filter(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        ts = _make_taskseries(name="Buy milk")
        tl = _make_task_list(taskseries=[ts])
        mock_client.get_tasks.return_value = _make_task_list_response([tl])
        service = self._make_service(rtm_settings, mock_client)

        result = service.list_tasks(filter_str="tag:work")
        data = json.loads(result)

        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["name"] == "Buy milk"
        mock_client.get_tasks.assert_called_once_with(filter_str="tag:work")

    def test_list_tasks_default_filter(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        ts = _make_taskseries(name="Buy milk")
        tl = _make_task_list(taskseries=[ts])
        mock_client.get_tasks.return_value = _make_task_list_response([tl])
        service = self._make_service(rtm_settings, mock_client)

        result = service.list_tasks()
        data = json.loads(result)

        assert len(data["tasks"]) == 1
        mock_client.get_tasks.assert_called_once_with(filter_str="status:incomplete")

    def test_list_tasks_empty(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        mock_client.get_tasks.return_value = _make_task_list_response(None)
        service = self._make_service(rtm_settings, mock_client)

        result = service.list_tasks()
        assert "No tasks found" in result

    def test_search_tasks(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        ts = _make_taskseries(name="Buy milk")
        tl = _make_task_list(taskseries=[ts])
        mock_client.get_tasks.return_value = _make_task_list_response([tl])
        service = self._make_service(rtm_settings, mock_client)

        result = service.search_tasks("milk")
        data = json.loads(result)

        assert len(data["tasks"]) == 1
        mock_client.get_tasks.assert_called_once_with(
            filter_str='status:incomplete AND name:"milk"'
        )

    def test_search_tasks_no_results(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        mock_client.get_tasks.return_value = _make_task_list_response(None)
        service = self._make_service(rtm_settings, mock_client)

        result = service.search_tasks("nonexistent")
        assert "No tasks matching" in result

    def test_list_tags(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        tag1 = MagicMock()
        tag1.name = "shopping"
        tag2 = MagicMock()
        tag2.name = "work"
        mock_client.get_tags.return_value.tags.tag = [tag1, tag2]
        service = self._make_service(rtm_settings, mock_client)

        result = service.list_tags()
        data = json.loads(result)

        assert data["tags"] == ["shopping", "work"]

    def test_list_tasks_sorted_by_priority(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        task_low = _make_task(task_id="t1", priority=PriorityEnum.Priority3)
        task_high = _make_task(task_id="t2", priority=PriorityEnum.Priority1)
        task_none = _make_task(task_id="t3", priority=PriorityEnum.NoPriority)
        task_med = _make_task(task_id="t4", priority=PriorityEnum.Priority2)

        ts1 = _make_taskseries(ts_id="ts1", name="Low task", tasks=[task_low])
        ts2 = _make_taskseries(ts_id="ts2", name="High task", tasks=[task_high])
        ts3 = _make_taskseries(ts_id="ts3", name="No prio task", tasks=[task_none])
        ts4 = _make_taskseries(ts_id="ts4", name="Medium task", tasks=[task_med])

        tl = _make_task_list(taskseries=[ts1, ts2, ts3, ts4])
        mock_client.get_tasks.return_value = _make_task_list_response([tl])
        service = self._make_service(rtm_settings, mock_client)

        result = service.list_tasks()
        data = json.loads(result)

        names = [t["name"] for t in data["tasks"]]
        assert names == ["High task", "Medium task", "Low task", "No prio task"]

    def test_list_tasks_limited_to_100(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        taskseries_list = []
        for i in range(150):
            task = _make_task(task_id=f"t{i}")
            ts = _make_taskseries(ts_id=f"ts{i}", name=f"Task {i}", tasks=[task])
            taskseries_list.append(ts)

        tl = _make_task_list(taskseries=taskseries_list)
        mock_client.get_tasks.return_value = _make_task_list_response([tl])
        service = self._make_service(rtm_settings, mock_client)

        result = service.list_tasks()
        data = json.loads(result)

        assert len(data["tasks"]) == 100

