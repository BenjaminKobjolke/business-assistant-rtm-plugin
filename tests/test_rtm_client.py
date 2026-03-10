"""Tests for RtmClient with mocked rtmilk API."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from rtmilk.models import PriorityEnum

from business_assistant_rtm.config import RtmSettings
from business_assistant_rtm.rtm_client import RtmClient


class TestRtmClient:
    def _make_client(
        self, settings: RtmSettings, mock_api: MagicMock
    ) -> RtmClient:
        """Create a client with a pre-injected mock API."""
        client = RtmClient(settings)
        client._api = mock_api
        return client

    def test_lazy_api_init(self, rtm_settings: RtmSettings) -> None:
        client = RtmClient(rtm_settings)
        assert client._api is None

    @patch("business_assistant_rtm.rtm_client.API")
    def test_get_api_creates_once(
        self, mock_api_cls: MagicMock, rtm_settings: RtmSettings
    ) -> None:
        client = RtmClient(rtm_settings)
        api1 = client._get_api()
        api2 = client._get_api()
        assert api1 is api2
        mock_api_cls.assert_called_once_with(
            "test_api_key", "test_shared_secret", "test_token"
        )

    def test_timeline_caching(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        mock_api.TimelinesCreate.return_value.timeline = "tl_123"
        client = self._make_client(rtm_settings, mock_api)

        tl1 = client._get_timeline()
        tl2 = client._get_timeline()

        assert tl1 == "tl_123"
        assert tl1 is tl2
        mock_api.TimelinesCreate.assert_called_once()

    def test_get_lists(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        client = self._make_client(rtm_settings, mock_api)

        result = client.get_lists()

        mock_api.ListsGetList.assert_called_once()
        assert result is mock_api.ListsGetList.return_value

    def test_get_tasks(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        client = self._make_client(rtm_settings, mock_api)

        result = client.get_tasks(filter_str="status:incomplete", list_id="123")

        mock_api.TasksGetList.assert_called_once_with(
            list_id="123", filter="status:incomplete"
        )
        assert result is mock_api.TasksGetList.return_value

    def test_get_tags(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        client = self._make_client(rtm_settings, mock_api)

        result = client.get_tags()

        mock_api.TagsGetList.assert_called_once()
        assert result is mock_api.TagsGetList.return_value

    def test_add_task(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        mock_api.TimelinesCreate.return_value.timeline = "tl_1"
        client = self._make_client(rtm_settings, mock_api)

        client.add_task("Buy milk", list_id="42", parse=True)

        mock_api.TasksAdd.assert_called_once_with(
            timeline="tl_1", name="Buy milk", list_id="42", parse=True
        )

    def test_complete_task(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        mock_api.TimelinesCreate.return_value.timeline = "tl_1"
        client = self._make_client(rtm_settings, mock_api)

        client.complete_task("100", "200", "300")

        mock_api.TasksComplete.assert_called_once_with(
            timeline="tl_1", list_id="100", taskseries_id="200", task_id="300"
        )

    def test_uncomplete_task(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        mock_api.TimelinesCreate.return_value.timeline = "tl_1"
        client = self._make_client(rtm_settings, mock_api)

        client.uncomplete_task("100", "200", "300")

        mock_api.TasksUncomplete.assert_called_once_with(
            timeline="tl_1", list_id="100", taskseries_id="200", task_id="300"
        )

    def test_delete_task(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        mock_api.TimelinesCreate.return_value.timeline = "tl_1"
        client = self._make_client(rtm_settings, mock_api)

        client.delete_task("100", "200", "300")

        mock_api.TasksDelete.assert_called_once_with(
            timeline="tl_1", list_id="100", taskseries_id="200", task_id="300"
        )

    def test_set_due_date(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        mock_api.TimelinesCreate.return_value.timeline = "tl_1"
        client = self._make_client(rtm_settings, mock_api)

        client.set_due_date("100", "200", "300", "tomorrow")

        mock_api.TasksSetDueDate.assert_called_once_with(
            timeline="tl_1",
            list_id="100",
            taskseries_id="200",
            task_id="300",
            due="tomorrow",
            parse=True,
        )

    def test_set_priority(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        mock_api.TimelinesCreate.return_value.timeline = "tl_1"
        client = self._make_client(rtm_settings, mock_api)

        client.set_priority("100", "200", "300", PriorityEnum.Priority1)

        mock_api.TasksSetPriority.assert_called_once_with(
            timeline="tl_1",
            list_id="100",
            taskseries_id="200",
            task_id="300",
            priority=PriorityEnum.Priority1,
        )

    def test_set_task_name(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        mock_api.TimelinesCreate.return_value.timeline = "tl_1"
        client = self._make_client(rtm_settings, mock_api)

        client.set_task_name("100", "200", "300", "New name")

        mock_api.TasksSetName.assert_called_once_with(
            timeline="tl_1",
            list_id="100",
            taskseries_id="200",
            task_id="300",
            name="New name",
        )

    def test_add_tags(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        mock_api.TimelinesCreate.return_value.timeline = "tl_1"
        client = self._make_client(rtm_settings, mock_api)

        client.add_tags("100", "200", "300", ["shopping", "urgent"])

        mock_api.TasksAddTags.assert_called_once_with(
            timeline="tl_1",
            list_id="100",
            taskseries_id="200",
            task_id="300",
            tags=["shopping", "urgent"],
        )

    def test_remove_tags(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        mock_api.TimelinesCreate.return_value.timeline = "tl_1"
        client = self._make_client(rtm_settings, mock_api)

        client.remove_tags("100", "200", "300", ["old_tag"])

        mock_api.TasksRemoveTags.assert_called_once_with(
            timeline="tl_1",
            list_id="100",
            taskseries_id="200",
            task_id="300",
            tags=["old_tag"],
        )

    def test_add_note(self, rtm_settings: RtmSettings) -> None:
        mock_api = MagicMock()
        mock_api.TimelinesCreate.return_value.timeline = "tl_1"
        client = self._make_client(rtm_settings, mock_api)

        client.add_note("100", "200", "300", "Note Title", "Note body text")

        mock_api.TasksNotesAdd.assert_called_once_with(
            timeline="tl_1",
            list_id="100",
            taskseries_id="200",
            task_id="300",
            note_title="Note Title",
            note_text="Note body text",
        )
