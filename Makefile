.PHONY: test lint typecheck format

test:
	python -m pytest -q

lint:
	ruff check .

typecheck:
	mypy src

format:
	ruff format .
