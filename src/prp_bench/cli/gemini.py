"""Gemini CLI runner implementation."""

import os
from pathlib import Path
from typing import Any

from ..config import get_settings
from ..models import Prompt
from .base import BaseRunner


class GeminiRunner(BaseRunner):
    """Runner for Google Gemini CLI tool.

    Executes prompts using the Gemini CLI with proper authentication
    and --yolo mode for non-interactive execution.
    """

    def __init__(self, base_path: Path | None = None, timeout_seconds: int = 600) -> None:
        """Initialize GeminiRunner with longer default timeout.

        Args:
            base_path: Base path for operations
            timeout_seconds: Default timeout (600s for Gemini)
        """
        super().__init__(base_path, timeout_seconds)

    @property
    def tool_name(self) -> str:
        """Name of the CLI tool."""
        return "gemini"

    @property
    def executable(self) -> str:
        """Executable name for Gemini CLI."""
        return "gemini"

    def get_command_args(self, prompt: Prompt) -> list[str]:
        """Build command arguments for Gemini CLI execution.

        Args:
            prompt: Prompt to execute

        Returns:
            List of command line arguments for gemini CLI
        """
        args = [
            "-p",  # Prompt mode
            prompt.prompt,  # The actual prompt text
            "--yolo",  # Non-interactive mode, auto-approve everything
        ]
        return args

    def get_authentication_env(self) -> dict[str, str]:
        """Get authentication environment variables for Gemini CLI.

        Returns:
            Dictionary with GOOGLE_API_KEY if available
        """
        env_vars = {}

        settings = get_settings()
        if settings.google_api_key:
            env_vars["GOOGLE_API_KEY"] = settings.google_api_key

        return env_vars

    def check_tool_available(self) -> bool:
        """Check if Gemini CLI is available and authenticated.

        Returns:
            True if Gemini CLI is available and has API key
        """
        # Check if executable exists
        if not super().check_tool_available():
            return False

        # Check if API key is configured
        api_key = os.getenv("GOOGLE_API_KEY") or get_settings().google_api_key
        return bool(api_key)

    def execute_in_directory(
        self,
        prompt: Prompt,
        working_dir: Path,
        env: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Execute Gemini CLI with authentication.

        Args:
            prompt: Prompt to execute
            working_dir: Working directory for execution
            env: Additional environment variables
            timeout_seconds: Override default timeout

        Returns:
            Dictionary with execution results including Gemini-specific info
        """
        # Merge authentication env with provided env
        full_env = self.get_authentication_env()
        if env:
            full_env.update(env)

        # Execute using base implementation
        result = super().execute_in_directory(
            prompt=prompt, working_dir=working_dir, env=full_env, timeout_seconds=timeout_seconds
        )

        # Add Gemini-specific result processing if needed
        if result["success"]:
            result["tool_specific"] = {
                "yolo_mode": True,
                "model_used": "gemini-pro",  # Default model
            }

        return result
