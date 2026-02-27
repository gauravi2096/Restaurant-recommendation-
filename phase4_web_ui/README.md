# Phase 4: Web UI

Static frontend for the Restaurant Recommendation flow: preferences form → POST /recommend → summary + restaurant cards.

## Run the UI

1. **Start the Phase 2 API** (from project root):
   ```bash
   python -m phase2_api --port 8000
   ```
2. **Serve the static files** (from project root or this folder):
   ```bash
   cd phase4_web_ui && python -m http.server 8080
   ```
3. Open **http://localhost:8080** in a browser. The app will call **http://localhost:8000** for recommendations.

To use a different API URL, set it before loading the page, e.g. in the browser console:
`window.__API_BASE__ = "http://localhost:8000";` then reload.

## Contents

| Path | Purpose |
|------|--------|
| `index.html` | Form: location (dropdown), price range (dropdown), min rating, cuisine (dropdown) + loading/error/results sections |
| `css/styles.css` | Responsive layout, dark theme |
| `js/config.js` | API base URL (default localhost:8000 when not same origin) |
| `js/api.js` | `buildRecommendRequest`, `fetchRecommend`, `parseRecommendResponse` |
| `js/app.js` | Form submit, loading/error/results UI, render restaurant cards |
| `js/types.js` | JSDoc types only |

## Tests

### Python (pytest, from project root)

```bash
pytest phase4_web_ui/tests -v
```

- **test_web_ui.py**: Static assets exist; request/response contract (body shape, response shape).
- **test_web_ui_integration.py**: POST /recommend returns `restaurants`, `summary`, `relaxed` and each restaurant has `name`, `location`, `rate`, `cost_for_two`, `url`.

### JavaScript (Vitest, optional)

If you have Node.js:

```bash
cd phase4_web_ui && npm install && npm test
```

Runs unit tests for `buildRecommendRequest`, `parseRecommendResponse`, and `fetchRecommend` (mocked).
