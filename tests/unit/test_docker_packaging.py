"""Static contracts for the optional Docker runtime packaging."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_CONTEXT = PROJECT_ROOT / "packaging" / "docker" / "test-repository-context"


def test_dockerfile_separates_production_and_test_targets() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "FROM base AS production" in dockerfile
    assert "FROM base AS test" in dockerfile
    assert "COPY requirements-dev.lock ./" in dockerfile
    assert "COPY . ." in dockerfile
    assert "test-repository-context/Dockerfile /app/Dockerfile" in dockerfile
    assert "test-repository-context/dockerignore /app/.dockerignore" in dockerfile
    assert "test-repository-context/ci.yml /app/.github/workflows/ci.yml" in dockerfile
    assert 'CMD ["pytest"]' in dockerfile
    assert "USER ebauteilefuchs" in dockerfile
    assert "alembic upgrade head" in (
        PROJECT_ROOT / "packaging" / "docker" / "entrypoint.sh"
    ).read_text(encoding="utf-8")
    assert "exec python -m ebauteilefuchs" in (
        PROJECT_ROOT / "packaging" / "docker" / "entrypoint.sh"
    ).read_text(encoding="utf-8")
    production_section = dockerfile.split("FROM base AS production", maxsplit=1)[
        1
    ].split("FROM base AS test", maxsplit=1)[0]
    assert "requirements-dev.lock" not in production_section
    assert "pytest" not in production_section
    assert "ruff" not in production_section


def test_compose_uses_production_app_and_isolated_test_profile() -> None:
    compose = (PROJECT_ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert "target: production" in compose
    assert "healthcheck:" in compose
    assert 'profiles: ["test"]' in compose
    assert "target: test" in compose
    assert "ebauteilefuchs-data:/data" in compose
    test_section = compose.split("  test:\n", maxsplit=1)[1].split(
        "\nvolumes:\n", maxsplit=1
    )[0]
    assert "ebauteilefuchs-data" not in test_section
    assert "EBAUTEILEFUCHS_APP_ENV: test" in test_section


def test_dockerignore_excludes_local_data_and_secrets() -> None:
    ignored = (PROJECT_ROOT / ".dockerignore").read_text(encoding="utf-8")

    for entry in (".env", "/data/", "/backups/", "*.sqlite3", "*.zip", "*.pdf"):
        assert entry in ignored


def test_test_repository_context_keeps_docker_control_files_in_sync() -> None:
    """Docker cannot COPY its own control files from the regular build context."""

    assert (TEST_CONTEXT / "Dockerfile").read_bytes() == (
        PROJECT_ROOT / "Dockerfile"
    ).read_bytes()
    assert (TEST_CONTEXT / "dockerignore").read_bytes() == (
        PROJECT_ROOT / ".dockerignore"
    ).read_bytes()
    assert (TEST_CONTEXT / "ci.yml").read_bytes() == (
        PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
    ).read_bytes()
