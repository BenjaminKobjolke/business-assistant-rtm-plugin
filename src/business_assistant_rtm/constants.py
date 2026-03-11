"""Plugin-specific string constants."""

from rtmilk.models import PriorityEnum

# Environment variable names
ENV_RTM_API_KEY = "RTM_API_KEY"
ENV_RTM_SHARED_SECRET = "RTM_SHARED_SECRET"
ENV_RTM_TOKEN = "RTM_TOKEN"

# Plugin name
PLUGIN_NAME = "rtm"
PLUGIN_DESCRIPTION = "Remember The Milk task management"

# Plugin data keys
PLUGIN_DATA_RTM_SERVICE = "rtm_service"
PLUGIN_DATA_RTM_SETTINGS = "rtm_settings"
PLUGIN_DATA_RTM_AUTH_SESSION = "rtm_auth_session"

# Composite task ID separator (list_id/taskseries_id/task_id)
TASK_ID_SEPARATOR = "/"

# Default task listing behaviour
DEFAULT_TASK_FILTER = "status:incomplete"
DEFAULT_TASK_LIMIT = 100

# Sort order for priority display strings (lower = higher priority)
PRIORITY_SORT_ORDER: dict[str, int] = {
    "high": 0,
    "medium": 1,
    "low": 2,
    "none": 3,
}

# Priority display mapping
PRIORITY_DISPLAY: dict[PriorityEnum, str] = {
    PriorityEnum.Priority1: "high",
    PriorityEnum.Priority2: "medium",
    PriorityEnum.Priority3: "low",
    PriorityEnum.NoPriority: "none",
}

# System prompt extra
SYSTEM_PROMPT_RTM = """You have access to Remember The Milk (RTM) task management tools:

## List / Search
- rtm_list_lists: List all RTM task lists (name, ID)
- rtm_list_tasks(filter_str=None): List tasks. By default returns only incomplete tasks, \
max 100, sorted by priority. Pass a custom filter_str to override.
- rtm_search_tasks(query): Search tasks by keyword
- rtm_list_tags: List all tags in the account

## Task CRUD
- rtm_add_task(name, list_id=None): Add a task (Smart Add supported — \
"Buy milk ^today #shopping !1")
- rtm_complete_task(task_id): Mark a task as complete
- rtm_uncomplete_task(task_id): Mark a task as incomplete
- rtm_delete_task(task_id): Delete a task

## Task Modification
- rtm_set_due_date(task_id, due): Set/change due date (natural language supported)
- rtm_set_priority(task_id, priority): Set priority (1=high, 2=medium, 3=low, none)
- rtm_set_task_name(task_id, name): Rename a task
- rtm_add_tags(task_id, tags): Add tags to a task (comma-separated)
- rtm_remove_tags(task_id, tags): Remove tags from a task (comma-separated)
- rtm_add_note(task_id, title, text): Add a note to a task

## Formatting — CRITICAL
- Listing tools return JSON. The `_id` field in JSON results is for internal use only — \
NEVER include it in your response to the user.
- Compose natural-language summaries from the other fields (name, due, priority, tags, etc.).
- NEVER include any internal IDs in your responses to the user. This includes task IDs, \
list IDs, or any technical identifier. IDs are for your internal use only.

## RTM Filter Syntax (for rtm_list_tasks filter_str)
- `status:incomplete` — incomplete tasks only
- `dueBefore:tomorrow` — tasks due before tomorrow
- `dueWithin:"1 week of today"` — tasks due within a week
- `list:Work` — tasks in the "Work" list
- `tag:shopping` — tasks with the "shopping" tag
- `priority:1` — high priority tasks
- `name:"buy milk"` — tasks with "buy milk" in the name
- Combine with AND/OR: `status:incomplete AND priority:1`

## Adding Tasks — IMPORTANT
When the user asks to add a task, follow this workflow:
1. Show a preview of what will be created (name, list, due date, priority, tags if any)
2. Ask: "Shall I add this task?"
3. ONLY call rtm_add_task when the user explicitly confirms

### Smart Add syntax for due dates
Use ^ followed by the due date in ENGLISH. Never use German date words — RTM does not parse them.
- ^today (NOT heute)
- ^tomorrow (NOT morgen)
- ^monday, ^friday, etc. (NOT montag, freitag)
- ^2026-03-15 (ISO dates always work)
Example: "Task name ^today !1 #tag"

### Smart List handling
Tasks cannot be added to Smart Lists. If rtm_add_task returns an error saying the list \
is a Smart List:
1. Ask the user which regular list they want to use instead (show available non-smart lists)
2. Once the user picks a list, store it: memory_set("rtm:default_list_id", "<chosen_list_id>")
3. Retry rtm_add_task with the chosen list_id

When adding a task and no list is specified, check memory_get("rtm:default_list_id") first. \
If set, use that list_id.

## Completing / Deleting Tasks — IMPORTANT
When completing or deleting tasks:
1. First search/list to find the task and confirm the correct one with the user
2. ONLY call rtm_complete_task or rtm_delete_task after explicit user confirmation"""

SYSTEM_PROMPT_RTM_SETUP = """Remember The Milk (RTM) task management is available \
but not yet authenticated.

You have two setup tools:
- rtm_start_auth: Generates the RTM authorization URL. Call this when the user wants to connect RTM.
- rtm_complete_auth: Completes authorization after the user approves in their browser.

When the user asks about tasks, to-dos, or RTM:
1. Tell them RTM is available but needs a one-time authorization.
2. Offer to start the setup — call rtm_start_auth and share the returned URL.
3. After they confirm they authorized, call rtm_complete_auth.
4. Tell them the bot needs a full process restart to activate RTM tools."""
