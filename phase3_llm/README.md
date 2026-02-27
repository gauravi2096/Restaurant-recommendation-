# Phase 3: Groq LLM Integration

Uses the Groq API to turn filtered restaurant results and user preferences into a short, readable recommendation summary. If the API key is missing or the call fails, the service returns `None` (Phase 2 then returns `summary: null`).

## Setup

1. Get an API key from [Groq Console](https://console.groq.com/).
2. Set it in the environment:
   ```bash
   export GROQ_API_KEY="your-key-here"
   ```
3. Install dependencies (from project root):
   ```bash
   pip install -r phase3_llm/requirements.txt
   ```

## Usage

### From Phase 2 API

When `GROQ_API_KEY` is set, the Phase 2 orchestrator automatically calls Phase 3 after filtering. The `POST /recommend` response will include a non-null `summary` when the LLM succeeds.

### Standalone

```python
from phase3_llm.service import generate_summary

restaurants = [{"name": "Jalsa", "location": "Banashankari", "rate": 4.1, "cost_for_two": 800, "cuisines": "North Indian", "dish_liked": "Pasta", "rest_type": "Casual Dining"}]
preferences = {"location": "Banashankari", "max_cost": 800}
summary = generate_summary(restaurants, preferences)
# summary is a string or None
```

### CLI test (when key is set)

```bash
python -m phase3_llm
```

## Module layout

| Module | Role |
|--------|------|
| `config.py` | `GROQ_API_KEY` env, default model (`llama-3.1-8b-instant`), timeout, max_tokens, retries. |
| `client.py` | `get_client(api_key, timeout)`, `create_completion(messages, ...)` with retries. |
| `prompt_builder.py` | `build_messages(restaurants, preferences)` → system + user messages for Groq. |
| `response_parser.py` | `parse_summary(raw_content)` → strip and optionally unwrap markdown. |
| `service.py` | `generate_summary(restaurants, preferences, api_key=None)` → summary or `None` (fallback on error). |

## Test cases

Test cases will be added once the Groq API key is integrated (e.g. mocked client or optional live tests).

## Config

- **Model**: `llama-3.1-8b-instant` (override via client if needed).
- **Timeout**: 30 seconds (client-level).
- **Max tokens**: 1024.
- **Retries**: 2 on transient errors.
