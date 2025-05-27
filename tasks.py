from invoke.tasks import task
from invoke.context import Context


@task
def lint(c: Context) -> None:
    """
    Format and lint
    """
    c.run("uv run ruff check src tests tasks.py --fix")
    c.run("uv run black src tests tasks.py")


@task
def type_check(c: Context) -> None:
    c.run("uv run mypy src tasks.py")


@task
def test(c: Context) -> None:
    c.run("uv run pytest tests --disable-warnings -v")


@task
def service_up(c: Context) -> None:
    c.run("uv run uvicorn src.local_llm_proxy.proxy_app:app --reload --host 0.0.0.0 --port 8000")


@task
def docker_build(c: Context) -> None:
    c.run("docker compose -f compose.yml build")


@task
def docker_up(c: Context) -> None:
    c.run("docker compose -f compose.yml up -d")


@task
def docker_down(c: Context) -> None:
    c.run("docker compose down")


@task
def build(c: Context) -> None:
    lint(c)
    type_check(c)
    test(c)


@task
def clean(c: Context) -> None:
    c.run('find . -type d -name "__pycache__" -exec rm -r {} + || true')
    c.run('find . -type d -name ".mypy_cache" -exec rm -r {} + || true')
    c.run('find . -type d -name ".ruff_cache" -exec rm -r {} + || true')
