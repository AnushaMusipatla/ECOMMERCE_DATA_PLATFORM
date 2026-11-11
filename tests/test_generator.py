"""Tests for seeded independent source generation."""

import pandas as pd

from generator.data_generator import generate


def test_larger_seeded_dataset_preserves_order_prefix(tmp_path):
    small_dir, large_dir = tmp_path / "small", tmp_path / "large"
    small_orders, small_customers = generate(small_dir, size=10, seed=99, include_edge_cases=False)
    large_orders, large_customers = generate(large_dir, size=20, seed=99, include_edge_cases=False)
    small_frame = pd.read_csv(small_orders, dtype=str)
    large_frame = pd.read_csv(large_orders, dtype=str)
    assert small_frame.equals(large_frame.iloc[:10].reset_index(drop=True))
    customer_ids = set(pd.read_csv(large_customers, dtype=str)["customer_id"])
    assert set(large_frame["customer_id"]).issubset(customer_ids)
