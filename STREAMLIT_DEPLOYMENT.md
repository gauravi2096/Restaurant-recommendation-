# Deploying on Streamlit

This project can be run and deployed as a Streamlit app.

## Local run

From the **repository root**:

```bash
# Install dependencies (if not already)
pip install -r requirements-streamlit.txt

# Optional: populate the database if empty
python -m phase1_data_pipeline --cache-dir ./phase1_data_pipeline/.hf_cache

# Run the app
streamlit run streamlit_app.py
```

Then open **http://localhost:8501** in your browser.

## Streamlit Community Cloud

1. **Push your repo to GitHub** (including `streamlit_app.py`, `requirements-streamlit.txt`, and the `phase1_data_pipeline`, `phase2_api`, `phase3_llm` packages).

2. **Go to [share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub.

3. **New app** → choose your repo, branch, and set:
   - **Main file path:** `streamlit_app.py`
   - **Advanced settings** → **Python version:** 3.9 or 3.10

4. **Requirements:** Use the repo root **`requirements.txt`** (or **`requirements-streamlit.txt`**). Both include Streamlit, FastAPI, Pydantic, Groq, and python-dotenv so the app and phase2_api load correctly.

5. **Database:** The app expects `phase1_data_pipeline/restaurants.db`. If the file is missing (e.g. on first deploy, since the DB is gitignored), the app will **create it on first run**: it runs the data pipeline once (with a subset of the dataset), then reloads. No manual setup or setup script is required. Optionally you can still pre-build the DB locally and commit it, or use a setup script.

6. **Secrets (optional):** For LLM summaries, set `GROQ_API_KEY` in Streamlit Cloud → App → Settings → Secrets.

7. **Deploy** and open the generated URL.

## Environment

- **`RESTAURANT_DB_PATH`** (optional): Path to the SQLite database. Defaults to `phase1_data_pipeline/restaurants.db` relative to the app root.
- **`GROQ_API_KEY`** (optional): For AI-generated summaries. If unset, the summary section is omitted.
