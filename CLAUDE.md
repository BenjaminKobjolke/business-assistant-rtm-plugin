# Business Assistant RTM Plugin - Development Guide

## Project Overview

Remember The Milk (RTM) plugin for Business Assistant v2. Source code in `src/business_assistant_rtm/`.

## Commands

- `uv sync --all-extras` — Install dependencies
- `uv run pytest tests/ -v` — Run tests
- `uv run ruff check src/ tests/` — Lint
- `uv run mypy src/` — Type check

## Architecture

- `config.py` — RtmSettings (frozen dataclass)
- `constants.py` — Plugin-specific string constants
- `rtm_client.py` — RtmClient (wraps rtmilk API with lazy init + timeline caching)
- `rtm_service.py` — High-level RTM operations (string-returning)
- `plugin.py` — Plugin registration + PydanticAI tool definitions
- `__init__.py` — Exposes `register()` as entry point

## Plugin Protocol

The plugin exposes `register(registry: PluginRegistry)` which:
1. Loads RTM settings from env vars (RTM_API_KEY, RTM_SHARED_SECRET, RTM_TOKEN)
2. Skips registration if RTM_API_KEY not configured
3. Creates RtmService and registers 14 PydanticAI tools (rtm_ prefixed)

## Restarting the Bot

After making code changes, always restart the bot by creating the restart flag:

```bash
touch "D:/GIT/BenjaminKobjolke/business-assistant-v2/restart.flag"
```

The bot picks it up within 5 seconds and restarts with fresh plugins.

## Code Analysis

After implementing new features or making significant changes, run the code analysis:

```bash
powershell -Command "cd 'D:\GIT\BenjaminKobjolke\business-assistant-rtm-plugin'; cmd /c '.\tools\analyze_code.bat'"
```

Fix any reported issues before committing.

## Rules

- Use objects for related values (DTOs/Settings)
- Centralize string constants in `constants.py`
- Tests are mandatory — use pytest with mocked rtmilk API
- Use `spec=` with MagicMock
- Type hints on all public APIs
- Frozen dataclasses for settings
