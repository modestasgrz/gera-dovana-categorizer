
.PHONY: check test clean

check:
	uv run ruff check src/ tests/
	@echo
	uv run ruff format src/ tests/ --diff --check
	@echo
	uv run mypy src/ tests/

test:
	uv run pytest --disable-pytest-warnings tests/

clean:
	rm -rf dist/ build/ *.spec
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
