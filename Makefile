.PHONY: install
install: ## Install the virtual environment
	@echo "Creating virtual environment using uv"
	@uv sync

.PHONY: check
check: ## Run code quality tools
	@echo "Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "Running ruff to lint code"
	@uv run ruff check src tests --fix
	@echo "Running black to format code"
	@uv run black src tests
	@echo "Static type checking: Running mypy"
	@uv run mypy src tests

.PHONY: check-no-fix
check-no-fix: ## Run code quality tools without fixing issues
	@echo "Checking lock file consistency with 'pyproject.toml'"
	@uv lock --check --offline
	@echo "Running ruff to lint code"
	@uv run ruff check src tests
	@echo "Running black to format code"
	@uv run black src tests --check
	@echo "Static type checking: Running mypy"
	@uv run mypy src tests

.PHONY: test
test: ## Test the code with pytest
	@echo "Testing code: Running pytest"
	@uv run pytest tests --disable-warnings -v

.PHONY: build
build: clean-build ## Build wheel file
	@echo "Creating wheel file"
	@uvx --from build pyproject-build --installer uv

.PHONY: clean-build
clean-build: ## Clean build artifacts
	@echo "Removing build artifacts"
	@uv run python -c "import shutil; import os; shutil.rmtree('dist') if os.path.exists('dist') else None"

.PHONY: publish
publish: ## Publish a release to PyPI
	@echo "Publishing."
	@uvx twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

.PHONY: run
run: ## Run the application
	@echo "Running the application"
	@uv run uvicorn src.prompt_passage.proxy_app:app --reload --host 0.0.0.0 --port 8095

.PHONY: help
help:
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.DEFAULT_GOAL := help