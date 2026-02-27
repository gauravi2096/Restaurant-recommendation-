"""Tests for the dataset loader."""

import pytest
from unittest.mock import patch, MagicMock

from phase1_data_pipeline.loader import (
    load_zomato_dataset,
    load_zomato_dataset_as_dicts,
    DATASET_ID,
    SPLIT,
)


class TestLoadZomatoDataset:
    """Test load_zomato_dataset with mocked Hugging Face."""

    @patch("phase1_data_pipeline.loader.load_dataset")
    def test_load_dataset_calls_hf_with_correct_params(self, mock_load):
        mock_ds = MagicMock()
        mock_load.return_value = mock_ds

        result = load_zomato_dataset(dataset_id="custom/dataset", split="train")

        mock_load.assert_called_once()
        call_kw = mock_load.call_args[1]
        assert call_kw.get("split") == "train"
        assert "streaming" in call_kw
        assert result is mock_ds

    @patch("phase1_data_pipeline.loader.load_dataset")
    def test_load_dataset_uses_default_id_and_split(self, mock_load):
        mock_ds = MagicMock()
        mock_load.return_value = mock_ds

        load_zomato_dataset()

        mock_load.assert_called_once_with(
            DATASET_ID,
            split=SPLIT,
            streaming=False,
            trust_remote_code=False,
        )

    @patch("phase1_data_pipeline.loader.load_dataset")
    def test_load_dataset_propagates_exception(self, mock_load):
        mock_load.side_effect = OSError("Network error")

        with pytest.raises(OSError, match="Network error"):
            load_zomato_dataset()


class TestLoadZomatoDatasetAsDicts:
    """Test load_zomato_dataset_as_dicts with mocked load."""

    @patch("phase1_data_pipeline.loader.load_zomato_dataset")
    def test_returns_list_of_dicts(self, mock_load):
        two_rows = [
            {"name": "R1", "location": "Banglore", "rate": "4.0/5"},
            {"name": "R2", "location": "Mumbai", "rate": "3.5/5"},
        ]
        mock_ds = MagicMock()
        mock_ds.__len__ = lambda _: 2
        mock_subset = MagicMock()
        mock_subset.__iter__ = lambda self: iter(two_rows)
        mock_ds.select = lambda r: mock_subset
        mock_load.return_value = mock_ds

        result = load_zomato_dataset_as_dicts(max_rows=10)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "R1"
        assert result[1]["name"] == "R2"

    @patch("phase1_data_pipeline.loader.load_zomato_dataset")
    def test_max_rows_limits_result(self, mock_load):
        mock_ds = MagicMock()
        mock_ds.__len__ = lambda _: 100
        mock_subset = MagicMock()
        mock_subset.__iter__ = lambda self: iter([{"name": f"R{i}"} for i in range(3)])
        mock_ds.select = lambda r: mock_subset
        mock_load.return_value = mock_ds

        result = load_zomato_dataset_as_dicts(max_rows=3)

        assert len(result) == 3
        assert result[0]["name"] == "R0"
        assert result[2]["name"] == "R2"
