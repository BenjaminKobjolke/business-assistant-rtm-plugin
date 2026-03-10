# Business Assistant RTM Plugin

Remember The Milk (RTM) task management plugin for [Business Assistant v2](https://github.com/BenjaminKobjolke/business-assistant-v2).

## Setup

1. Install dependencies:
   ```bash
   uv sync --all-extras
   ```

2. Copy `.env.example` to `.env` and fill in your RTM credentials:
   ```
   RTM_API_KEY=your_api_key_here
   RTM_SHARED_SECRET=your_shared_secret_here
   RTM_TOKEN=your_token_here
   ```

3. Add `business_assistant_rtm` to the `PLUGINS` list in the main bot's `.env`.

## Tools Provided

- **rtm_list_lists** — List all RTM task lists
- **rtm_list_tasks** — List tasks with optional RTM filter
- **rtm_search_tasks** — Search tasks by keyword
- **rtm_list_tags** — List all tags
- **rtm_add_task** — Add a task (Smart Add supported)
- **rtm_complete_task** — Mark task complete
- **rtm_uncomplete_task** — Mark task incomplete
- **rtm_delete_task** — Delete a task
- **rtm_set_due_date** — Set/change due date
- **rtm_set_priority** — Set priority
- **rtm_set_task_name** — Rename a task
- **rtm_add_tags** — Add tags to a task
- **rtm_remove_tags** — Remove tags from a task
- **rtm_add_note** — Add a note to a task

## Development

```bash
uv run pytest tests/ -v
uv run ruff check src/ tests/
uv run mypy src/
```
