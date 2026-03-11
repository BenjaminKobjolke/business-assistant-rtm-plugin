"""Tests for RtmService mutation operations (add, complete, delete, set, tags, notes)."""

from __future__ import annotations

from unittest.mock import MagicMock

from business_assistant_rtm.config import RtmSettings
from business_assistant_rtm.rtm_service import RtmService


class TestRtmServiceMutations:
    def _make_service(
        self, settings: RtmSettings, mock_client: MagicMock
    ) -> RtmService:
        """Create a service with a pre-injected mock client."""
        service = RtmService(settings)
        service._client = mock_client
        return service

    def test_add_task(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        mock_ts = MagicMock()
        mock_ts.name = "Buy milk"
        mock_client.add_task.return_value.list.taskseries = [mock_ts]
        service = self._make_service(rtm_settings, mock_client)

        result = service.add_task("Buy milk tomorrow #shopping")

        assert "Task added" in result
        assert "Buy milk" in result
        mock_client.add_task.assert_called_once_with(
            name="Buy milk tomorrow #shopping", list_id=None
        )

    def test_complete_task(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        service = self._make_service(rtm_settings, mock_client)

        result = service.complete_task("100/200/300")

        assert "complete" in result
        mock_client.complete_task.assert_called_once_with("100", "200", "300")

    def test_uncomplete_task(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        service = self._make_service(rtm_settings, mock_client)

        result = service.uncomplete_task("100/200/300")

        assert "incomplete" in result
        mock_client.uncomplete_task.assert_called_once_with("100", "200", "300")

    def test_delete_task(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        service = self._make_service(rtm_settings, mock_client)

        result = service.delete_task("100/200/300")

        assert "deleted" in result
        mock_client.delete_task.assert_called_once_with("100", "200", "300")

    def test_set_due_date(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        service = self._make_service(rtm_settings, mock_client)

        result = service.set_due_date("100/200/300", "tomorrow")

        assert "Due date set" in result
        mock_client.set_due_date.assert_called_once_with("100", "200", "300", "tomorrow")

    def test_set_priority(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        service = self._make_service(rtm_settings, mock_client)

        result = service.set_priority("100/200/300", "1")

        assert "high" in result
        mock_client.set_priority.assert_called_once()

    def test_set_priority_invalid(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        service = self._make_service(rtm_settings, mock_client)

        result = service.set_priority("100/200/300", "invalid")

        assert "Invalid priority" in result

    def test_set_task_name(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        service = self._make_service(rtm_settings, mock_client)

        result = service.set_task_name("100/200/300", "New Name")

        assert "renamed" in result
        mock_client.set_task_name.assert_called_once_with("100", "200", "300", "New Name")

    def test_add_tags(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        service = self._make_service(rtm_settings, mock_client)

        result = service.add_tags("100/200/300", "shopping, urgent")

        assert "Tags added" in result
        mock_client.add_tags.assert_called_once_with(
            "100", "200", "300", ["shopping", "urgent"]
        )

    def test_remove_tags(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        service = self._make_service(rtm_settings, mock_client)

        result = service.remove_tags("100/200/300", "old_tag")

        assert "Tags removed" in result
        mock_client.remove_tags.assert_called_once_with(
            "100", "200", "300", ["old_tag"]
        )

    def test_add_note(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        service = self._make_service(rtm_settings, mock_client)

        result = service.add_note("100/200/300", "My Note", "Note body")

        assert "Note" in result
        assert "added" in result
        mock_client.add_note.assert_called_once_with(
            "100", "200", "300", "My Note", "Note body"
        )

    def test_complete_task_invalid_id(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        service = self._make_service(rtm_settings, mock_client)

        result = service.complete_task("invalid_id")

        assert "Error" in result

    def test_add_task_smart_list_returns_error(self, rtm_settings: RtmSettings) -> None:
        """When list_id is a smart list, add_task returns an error message."""
        mock_client = MagicMock()
        smart_list = MagicMock()
        smart_list.id = "42"
        smart_list.name = "Focus XIDA"
        smart_list.smart = True
        mock_client.get_lists.return_value.lists.list = [smart_list]
        service = self._make_service(rtm_settings, mock_client)

        result = service.add_task("Buy milk", list_id="42")

        assert "Smart List" in result
        assert "Focus XIDA" in result
        mock_client.add_task.assert_not_called()

    def test_add_task_regular_list_passes_through(self, rtm_settings: RtmSettings) -> None:
        """When list_id is a regular list, it is passed through unchanged."""
        mock_client = MagicMock()
        regular_list = MagicMock()
        regular_list.id = "99"
        regular_list.name = "Work"
        regular_list.smart = False
        mock_client.get_lists.return_value.lists.list = [regular_list]
        mock_ts = MagicMock()
        mock_ts.name = "Buy milk"
        mock_client.add_task.return_value.list.taskseries = [mock_ts]
        service = self._make_service(rtm_settings, mock_client)

        result = service.add_task("Buy milk", list_id="99")

        assert "Task added" in result
        mock_client.add_task.assert_called_once_with(name="Buy milk", list_id="99")

    def test_list_lists_error(self, rtm_settings: RtmSettings) -> None:
        mock_client = MagicMock()
        mock_client.get_lists.side_effect = Exception("API error")
        service = self._make_service(rtm_settings, mock_client)

        result = service.list_lists()

        assert "Error" in result
