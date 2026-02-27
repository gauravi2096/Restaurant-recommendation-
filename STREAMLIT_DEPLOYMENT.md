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

4. **Requirements:** In "Advanced settings", set **Requirements file** to `requirements-streamlit.txt` (or create a root `requirements.txt` that includes the same dependencies).

5. **Database:** The app expects `phase1_data_pipeline/restaurants.db`. Either:
   - **Option A:** Run the pipeline locally, commit `phase1_data_pipeline/restaurants.db` (if acceptable size), and deploy.
   - **Option B:** Add a **Setup script** in Streamlit Cloud that runs the pipeline on deploy (e.g. a shell script that runs `python -m phase1_data_pipeline --max-rows 5000`). This requires adding `datasets`, `pandas`, and `huggingface_hub` to `requirements-streamlit.txt` and may increase deploy time.

6. **Secrets (optional):** For LLM summaries, set `GROQ_API_KEY` in Streamlit Cloud → App → Settings → Secrets.

7. **Deploy** and open the generated URL.

## Environment

- **`RESTAURANT_DB_PATH`** (optional): Path to the SQLite database. Defaults to `phase1_data_pipeline/restaurants.db` relative to the app root.
- **`GROQ_API_KEY`** (optional): For AI-generated summaries. If unset, the summary section is omitted.
