"""Claude Code CLI runner implementation."""

import os
from pathlib import Path
from typing import Any

from ..config import get_settings
from ..models import Prompt
from .base import BaseRunner


class ClaudeRunner(BaseRunner):
    """Runner for Claude Code CLI tool.

    Executes prompts using the Claude Code CLI with proper authentication,
    permissions handling, and telemetry integration.
    """

    @property
    def tool_name(self) -> str:
        """Name of the CLI tool."""
        return "claude"

    @property
    def executable(self) -> str:
        """Executable name for Claude Code."""
        return "claude"

    def get_command_args(self, prompt: Prompt) -> list[str]:
        """Build command arguments for Claude Code execution.

        Args:
            prompt: Prompt to execute

        Returns:
            List of command line arguments for claude CLI
        """
        args = [
            "--dangerously-skip-permissions",  # Skip permission prompts for automation
            "-p",  # Prompt mode
            prompt.prompt,  # The actual prompt text
        ]
        return args

    def get_authentication_env(self) -> dict[str, str]:
        """Get authentication environment variables for Claude Code.

        Returns:
            Dictionary with ANTHROPIC_API_KEY if available
        """
        env_vars = {}

        settings = get_settings()
        if settings.anthropic_api_key:
            env_vars["ANTHROPIC_API_KEY"] = settings.anthropic_api_key

        # Add telemetry configuration if enabled
        env_vars.update(settings.get_telemetry_env_vars())

        return env_vars

    def check_tool_available(self) -> bool:
        """Check if Claude Code CLI is available and authenticated.

        Returns:
            True if Claude Code is available and has API key
        """
        # Check if executable exists
        if not super().check_tool_available():
            return False

        # Check if API key is configured
        api_key = os.getenv("ANTHROPIC_API_KEY") or get_settings().anthropic_api_key
        return bool(api_key)

    def execute_in_directory(
        self,
        prompt: Prompt,
        working_dir: Path,
        env: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Execute Claude Code with authentication and telemetry.

        Args:
            prompt: Prompt to execute
            working_dir: Working directory for execution
            env: Additional environment variables
            timeout_seconds: Override default timeout

        Returns:
            Dictionary with execution results including Claude-specific info
        """
        # Merge authentication env with provided env
        full_env = self.get_authentication_env()
        if env:
            full_env.update(env)

        # Execute using base implementation
        result = super().execute_in_directory(
            prompt=prompt, working_dir=working_dir, env=full_env, timeout_seconds=timeout_seconds
        )

        # Add Claude-specific result processing if needed
        if result["success"]:
            result["tool_specific"] = {
                "telemetry_enabled": bool(full_env.get("CLAUDE_CODE_ENABLE_TELEMETRY")),
                "model_used": full_env.get("CLAUDE_CODE_SDK_MODEL", "default"),
            }

        return result
