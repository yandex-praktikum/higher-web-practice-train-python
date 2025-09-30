run:
	python main.py

linter:
	ruff check ./sorting_handler

test:
	pytest tests

sync:
	uv sync
