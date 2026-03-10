# RTM Plugin — In-Chat OAuth Authentication

## Prerequisites

- `RTM_API_KEY` and `RTM_SHARED_SECRET` set in `.env`
- These come from the [RTM API page](https://www.rememberthemilk.com/services/api/)

## How Setup Mode Activates

When the bot starts, the RTM plugin checks for a valid token:

1. If `RTM_API_KEY` is missing → plugin skips registration entirely
2. If `RTM_API_KEY` is set but no token exists (`data/rtm_token` missing, `RTM_TOKEN` empty) → **setup mode**: 2 auth tools registered
3. If token exists → **normal mode**: 14 task management tools registered

## In-Chat OAuth Flow

```
User                    Bot                     RTM API
  |                      |                        |
  |  "connect RTM"       |                        |
  |--------------------->|                        |
  |                      |  getFrob()             |
  |                      |----------------------->|
  |                      |  <frob>                |
  |                      |<-----------------------|
  |  auth URL            |                        |
  |<---------------------|                        |
  |                      |                        |
  |  opens URL in browser, clicks "Allow"         |
  |---------------------------------------------->|
  |                      |                        |
  |  "done"              |                        |
  |--------------------->|                        |
  |                      |  getToken(frob)        |
  |                      |----------------------->|
  |                      |  <token>               |
  |                      |<-----------------------|
  |  "authorized!"       |                        |
  |<---------------------|                        |
```

### Step 1: `rtm_start_auth`

- Creates an `AuthorizationSession` (from `rtmilk`) with the API key, shared secret, and `"delete"` permission level
- The session calls `getFrob()` internally and builds the authorization URL
- Stores the session in `plugin_data` for the second step
- Returns the URL for the user to open

### Step 2: `rtm_complete_auth`

- Retrieves the stored `AuthorizationSession`
- Calls `session.Done()` which exchanges the frob for a permanent token via `getToken()`
- Saves the token to `data/rtm_token`
- Cleans up the session from `plugin_data`

## Token Persistence

The token is saved to `data/rtm_token` as a plain text file. On next startup, the plugin auto-loads tokens from the `data/` directory (see `config.py` — `_load_token_from_file()`).

## Post-Auth: Restart Required

After successful authorization, the bot must be **fully stopped and restarted** (`Ctrl+C`, then `uv run python -m business_assistant.main`). The `restart.flag` mechanism only reloads code changes — it does not re-run plugin registration. A full restart is needed to switch from the 2 setup tools to the 14 task tools.

## Error Handling

- If the user hasn't clicked "Allow" yet when `rtm_complete_auth` is called, `session.Done()` raises an exception → the bot tells the user to try again
- If the frob expires or the API is unreachable, the error message is forwarded to the user
- The user can always retry by calling `rtm_start_auth` again (generates a new frob)

## Architecture: AuthorizationSession

RTM uses OAuth 1.0a-style authentication (not standard OAuth2):

1. **getFrob**: Obtains a temporary frob (request token)
2. **Auth URL**: User visits `rememberthemilk.com/services/auth/?frob=...&api_sig=...`
3. **getToken**: Exchanges the approved frob for a permanent auth token

The `rtmilk.AuthorizationSession` class encapsulates this flow. The plugin splits it across two chat interactions by storing the session object between calls.
