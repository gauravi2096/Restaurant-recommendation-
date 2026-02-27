"""Integration tests for the full pipeline."""

import pytest
from unittest.mock import patch

from phase1_data_pipeline.pipeline import run_pipeline
from phase1_data_pipeline.store import RestaurantStore


class TestRunPipeline:
    """Test run_pipeline with mocked loader (no real HF download in tests)."""

    @patch("phase1_data_pipeline.pipeline.load_zomato_dataset_as_dicts")
    def test_pipeline_loads_normalizes_and_stores(
        self, mock_load, temp_db_path, sample_raw_rows
    ):
        mock_load.return_value = sample_raw_rows

        result = run_pipeline(
            db_path=temp_db_path,
            max_rows=10,
            clear_before=True,
        )

        assert result["loaded_rows"] == len(sample_raw_rows)
        assert result["normalized_count"] >= 1
        assert result["inserted_count"] == result["normalized_count"]
        assert "db_path" in result

        store = RestaurantStore(temp_db_path)
        store.connect()
        try:
            assert store.count() == result["inserted_count"]
            rows = store.query(limit=5)
            assert len(rows) <= 5
            if rows:
                assert "name" in rows[0]
                assert "rate" in rows[0]
        finally:
            store.close()

    @patch("phase1_data_pipeline.pipeline.load_zomato_dataset_as_dicts")
    def test_pipeline_empty_data_returns_zeros(self, mock_load, temp_db_path):
        mock_load.return_value = []

        result = run_pipeline(db_path=temp_db_path, clear_before=True)

        assert result["loaded_rows"] == 0
        assert result["normalized_count"] == 0
        assert result["inserted_count"] == 0

    @patch("phase1_data_pipeline.pipeline.load_zomato_dataset_as_dicts")
    def test_pipeline_clear_before_false_appends(self, mock_load, temp_db_path, sample_raw_rows):
        mock_load.return_value = sample_raw_rows
        run_pipeline(db_path=temp_db_path, clear_before=True)
        store = RestaurantStore(temp_db_path)
        store.connect()
        first_count = store.count()
        store.close()

        run_pipeline(db_path=temp_db_path, clear_before=False)
        store = RestaurantStore(temp_db_path)
        store.connect()
        second_count = store.count()
        store.close()
        assert second_count == 2 * first_count
