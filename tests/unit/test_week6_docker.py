from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestDockerfiles:
    """Tests for Docker configuration files."""

    def test_dockerfile_exists(self):
        """Dockerfile should exist in project root."""
        dockerfile = PROJECT_ROOT / "Dockerfile"
        assert dockerfile.exists(), f"Dockerfile not found at {dockerfile}"

    def test_dockerfile_has_python_base(self):
        """Dockerfile should use Python base image."""
        dockerfile = PROJECT_ROOT / "Dockerfile"
        content = dockerfile.read_text()

        assert "FROM python" in content or "FROM python:" in content.lower()

    def test_docker_compose_exists(self):
        """docker-compose.yml should exist."""
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        assert compose_file.exists(), f"docker-compose.yml not found at {compose_file}"

    def test_dockerignore_exists(self):
        """dockerignore should exist to reduce image size."""
        dockerignore = PROJECT_ROOT / ".dockerignore"
        assert dockerignore.exists(), f".dockerignore not found at {dockerignore}"
