"""Tests for raw source preservation."""
from src.ingest import read_source
import pytest

def test_ingest_keeps_raw_bytes(sample_sources,tmp_path):
    orders,_=sample_sources
    rows,name=read_source(orders,"run",tmp_path/"raw")
    assert name == "orders.csv" and rows[0]["order_id"] == "O1"
    assert (tmp_path/"raw"/"run"/"orders.csv").read_bytes() == orders.read_bytes()

def test_empty_file_with_wrong_header_fails(tmp_path):
    source=tmp_path/"orders.csv"
    source.write_text("order_id,customer_id\n",encoding="utf-8")
    with pytest.raises(ValueError,match="Unexpected orders.csv schema"):
        read_source(source,"bad",tmp_path/"raw")
