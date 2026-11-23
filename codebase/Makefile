.PHONY: setup pipeline test build app
setup:
	scripts/setup.sh
pipeline:
	scripts/run_pipeline.sh
test:
	.venv/bin/python -m pytest -q backend/tests tests 2>/dev/null || .venv/bin/python -m pytest -q backend/tests
build:
	cd frontend && npm run build
app:
	scripts/run_app.sh
