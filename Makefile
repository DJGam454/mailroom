.PHONY: install seed run test check sync-sheets

install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

seed:
	.venv/bin/python -m app.seed

run:
	.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 4600 --reload

test:
	.venv/bin/python -m pytest -q

sync-sheets:
	.venv/bin/python scripts/sync_sheets.py --sync

check:
	.venv/bin/python -m py_compile app/*.py app/routes/*.py app/services/*.py
	node --check app/static/app.js
	.venv/bin/python -m pytest -q
