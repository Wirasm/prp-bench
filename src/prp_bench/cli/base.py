"""Abstract base class for CLI tool runners."""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..models import Prompt


class BaseRunner(ABC):
    """Abstract base class for AI CLI tool runners.

    Provides common functionality for executing AI coding tools in isolated
    environments with proper timeout and error handling.
    """

    def __init__(self, base_path: Path | None = None, timeout_seconds: int = 300) -> None:
        """Initialize base runner.

        Args:
            base_path: Base path for operations
            timeout_seconds: Default timeout for tool execution
        """
        self.base_path = base_path or Path.cwd()
        self.timeout_seconds = timeout_seconds

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Name of the CLI tool (e.g., 'claude', 'gemini')."""

    @property
    @abstractmethod
    def executable(self) -> str:
        """Executable name or path for the CLI tool."""

    @abstractmethod
    def get_command_args(self, prompt: Prompt) -> list[str]:
        """Build command arguments for executing the prompt.

        Args:
            prompt: Prompt to execute

        Returns:
            List of command line arguments
        """

    def check_tool_available(self) -> bool:
        """Check if the CLI tool is available and properly configured.

        Returns:
            True if tool is available, False otherwise
        """
        try:
            result = subprocess.run(
                [self.executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def execute_in_directory(
        self,
        prompt: Prompt,
        working_dir: Path,
        env: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Execute the tool with a prompt in a specific directory.

        Args:
            prompt: Prompt to execute
            working_dir: Working directory for execution
            env: Environment variables (merged with current env)
            timeout_seconds: Override default timeout

        Returns:
            Dictionary with execution results
        """
        timeout = timeout_seconds or self.timeout_seconds
        cmd = [self.executable, *self.get_command_args(prompt)]

        # Setup environment
        import os

        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        try:
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                env=full_env,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd),
                "timeout_used": False,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "command": " ".join(cmd),
                "timeout_used": True,
            }

        except Exception as e:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": f"Execution error: {e}",
                "command": " ".join(cmd),
                "timeout_used": False,
            }

    def get_authentication_env(self) -> dict[str, str]:
        """Get environment variables needed for authentication.

        Override this method in subclasses to provide tool-specific
        authentication setup.

        Returns:
            Dictionary of environment variables
        """
        return {}
