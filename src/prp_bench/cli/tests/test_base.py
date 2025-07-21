"""Tests for base CLI runner functionality."""

from pathlib import Path

from prp_bench.cli.base import BaseRunner
from prp_bench.models import ComplexityLevel, Prompt, PromptType


class MockRunner(BaseRunner):
    """Mock implementation of BaseRunner for testing."""

    def __init__(self, *args, executable="echo", **kwargs):
        super().__init__(*args, **kwargs)
        self._executable = executable

    @property
    def tool_name(self) -> str:
        return "test"

    @property
    def executable(self) -> str:
        return self._executable

    def get_command_args(self, prompt: Prompt) -> list[str]:
        return ["test output"]


class TestBaseRunner:
    """Test suite for BaseRunner abstract base class."""

    def test_init_default_path(self):
        """Test runner initialization with default path."""
        runner = MockRunner()
        assert runner.base_path == Path.cwd()
        assert runner.timeout_seconds == 300

    def test_init_custom_path(self):
        """Test runner initialization with custom path."""
        custom_path = Path("/tmp")
        runner = MockRunner(base_path=custom_path, timeout_seconds=600)
        assert runner.base_path == custom_path
        assert runner.timeout_seconds == 600

    def test_tool_properties(self):
        """Test tool name and executable properties."""
        runner = MockRunner()
        assert runner.tool_name == "test"
        assert runner.executable == "echo"

    def test_check_tool_available(self):
        """Test tool availability check."""
        runner = MockRunner()
        # echo command should be available on most systems
        assert runner.check_tool_available() is True

        # Test with non-existent command
        runner = MockRunner(executable="nonexistent_command_12345")
        assert runner.check_tool_available() is False

    def test_execute_in_directory(self, tmp_path):
        """Test execution in specific directory."""
        runner = MockRunner()
        prompt = Prompt(
            name="Test Prompt",
            description="Test description",
            type=PromptType.FEATURE,
            complexity=ComplexityLevel.SIMPLE,
            prompt="test prompt content",
        )

        result = runner.execute_in_directory(prompt, tmp_path)

        assert isinstance(result, dict)
        assert "success" in result
        assert "return_code" in result
        assert "stdout" in result
        assert "stderr" in result
        assert "command" in result
        assert result["success"] is True  # echo should succeed
        assert "test output" in result["stdout"]

    def test_get_authentication_env(self):
        """Test authentication environment variables."""
        runner = MockRunner()
        env = runner.get_authentication_env()
        assert isinstance(env, dict)
