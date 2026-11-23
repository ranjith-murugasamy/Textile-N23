import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import main  # noqa: E402


def test_health_and_empty_results(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "RESULTS", tmp_path)
    c = TestClient(main.app)
    assert c.get("/api/health").json()["has_metrics"] is False
    assert c.get("/api/metrics").status_code == 404
    assert c.get("/api/figures").json() == []


def test_serves_results(tmp_path, monkeypatch):
    (tmp_path / "figures").mkdir(); (tmp_path / "tables").mkdir()
    (tmp_path / "metrics.json").write_text(json.dumps({"headline": {"F1": 0.9}}))
    (tmp_path / "figures" / "fig_a.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (tmp_path / "figures" / "fig_a.md").write_text("Explains A")
    (tmp_path / "tables" / "t.csv").write_text("a,b\n1,2\n")
    monkeypatch.setattr(main, "RESULTS", tmp_path)
    c = TestClient(main.app)
    assert c.get("/api/metrics").json()["headline"]["F1"] == 0.9
    fig = c.get("/api/figures").json()[0]
    assert fig["explanation"] == "Explains A" and c.get(fig["url"]).status_code == 200
    assert c.get("/api/figures/../metrics.json").status_code == 404
    assert c.get("/api/tables").json()["t"][1] == ["1", "2"]
