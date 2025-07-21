"""Configuration management for PRP-Bench with Claude Code SDK integration."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class TelemetryConfig(BaseModel):
    """OpenTelemetry configuration for Claude Code SDK."""

    enabled: bool = Field(default=True, description="Enable telemetry collection")
    metrics_exporter: str = Field(default="console", description="OTel metrics exporter")
    traces_exporter: str = Field(default="console", description="OTel traces exporter")
    endpoint: str | None = Field(default=None, description="OTLP endpoint URL")
    service_name: str = Field(default="prp-bench", description="Service name for telemetry")
    service_version: str = Field(default="0.1.0", description="Service version")
    export_interval: int = Field(default=5000, description="Export interval in milliseconds")


class ToolConfig(BaseModel):
    """Configuration for individual tools."""

    name: str
    executable: str
    default_timeout: int = Field(default=300, description="Default timeout in seconds")
    flags: list[str] = Field(default_factory=list, description="Default CLI flags")
    env_vars: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    mcp_server: bool = Field(default=False, description="Tool is available as MCP server")


class LLMConfig(BaseModel):
    """LLM-specific configuration for prompt processing."""

    enabled: bool = Field(default=True, description="Enable LLM extraction")
    model: str = Field(default="claude-3-5-haiku-20241022", description="Fast model for extraction")
    timeout_seconds: int = Field(default=30, description="LLM call timeout")
    max_retries: int = Field(default=3, description="Retry attempts")
    confidence_threshold: float = Field(default=0.6, description="Min confidence for acceptance")
    fallback_enabled: bool = Field(default=True, description="Use fallbacks when LLM fails")


class ClaudeCodeConfig(BaseModel):
    """Claude Code SDK specific configuration."""

    permissions_mode: str = Field(default="dangerously-skip", description="Permission mode")
    max_turns: int = Field(default=10, description="Maximum conversation turns")
    model: str = Field(default="claude-3-5-sonnet-20241022", description="Default model")
    enable_streaming: bool = Field(default=False, description="Enable streaming responses")
    json_output: bool = Field(default=True, description="Use JSON output format")


class WorktreeConfig(BaseModel):
    """Git worktree configuration."""

    base_dir: Path = Field(default=Path("tmp/trees"), description="Base directory for worktrees")
    cleanup_on_exit: bool = Field(default=False, description="Auto cleanup worktrees")
    preserve_on_error: bool = Field(default=True, description="Preserve worktrees on errors")
    branch_prefix: str = Field(default="benchmark", description="Branch name prefix")


class Settings(BaseSettings):
    """Main application settings with environment variable support."""

    # Base configuration
    base_path: Path = Field(default_factory=Path.cwd, description="Base project path")
    debug: bool = Field(default=False, description="Debug mode")
    verbose: bool = Field(default=False, description="Verbose output")

    # Telemetry settings
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)

    # LLM settings for prompt processing
    llm: LLMConfig = Field(default_factory=LLMConfig)

    # Claude Code SDK settings
    claude_code: ClaudeCodeConfig = Field(default_factory=ClaudeCodeConfig)

    # Worktree settings
    worktree: WorktreeConfig = Field(default_factory=WorktreeConfig)

    # Tool configurations
    tools: dict[str, ToolConfig] = Field(default_factory=dict)

    # API keys and authentication
    anthropic_api_key: str | None = Field(default=None, description="Anthropic API key")
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    google_api_key: str | None = Field(default=None, description="Google API key")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "env_nested_delimiter": "__",
        "extra": "ignore",
    }

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings with default tool configurations."""
        super().__init__(**kwargs)

        # Set up default tool configurations if not provided
        if not self.tools:
            self.tools = self._get_default_tool_configs()

    def _get_default_tool_configs(self) -> dict[str, ToolConfig]:
        """Get default configurations for supported tools."""
        return {
            "claude": ToolConfig(
                name="claude",
                executable="claude",
                default_timeout=300,
                flags=["--dangerously-skip-permissions", "-p"],
                env_vars={"ANTHROPIC_API_KEY": self.anthropic_api_key or ""},
            ),
            "gemini": ToolConfig(
                name="gemini",
                executable="gemini",
                default_timeout=600,
                flags=["-p", "--yolo"],
                env_vars={"GOOGLE_API_KEY": self.google_api_key or ""},
                mcp_server=True,  # Future: Gemini will be available as MCP server
            ),
            "codex": ToolConfig(
                name="codex",
                executable="codex",
                default_timeout=600,
                flags=["exec", "--dangerously-auto-approve-everything"],
                env_vars={"OPENAI_API_KEY": self.openai_api_key or ""},
            ),
        }

    def get_telemetry_env_vars(self) -> dict[str, str]:
        """Get environment variables for OpenTelemetry configuration."""
        if not self.telemetry.enabled:
            return {}

        env_vars = {
            "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
            "OTEL_METRICS_EXPORTER": self.telemetry.metrics_exporter,
            "OTEL_TRACES_EXPORTER": self.telemetry.traces_exporter,
            "OTEL_RESOURCE_ATTRIBUTES": (
                f"service.name={self.telemetry.service_name},"
                f"service.version={self.telemetry.service_version}"
            ),
        }

        if self.telemetry.endpoint:
            env_vars["OTEL_EXPORTER_OTLP_ENDPOINT"] = self.telemetry.endpoint

        if self.telemetry.export_interval != 5000:
            env_vars["OTEL_METRIC_EXPORT_INTERVAL"] = str(self.telemetry.export_interval)

        return env_vars

    def get_llm_env_vars(self) -> dict[str, str]:
        """Get environment variables for LLM-powered prompt processing."""
        # Start with telemetry env vars since LLM calls use Claude Code SDK
        env_vars = self.get_telemetry_env_vars()

        if self.llm.enabled:
            env_vars.update(
                {
                    "CLAUDE_CODE_SDK_TIMEOUT": str(self.llm.timeout_seconds),
                    "CLAUDE_CODE_SDK_MODEL": self.llm.model,
                }
            )

        return env_vars

    def get_tool_config(self, tool_name: str) -> ToolConfig | None:
        """Get configuration for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool configuration or None if not found
        """
        return self.tools.get(tool_name)

    def get_worktree_path(self, session_id: str, tool_name: str) -> Path:
        """Get worktree path for a tool in a session.

        Args:
            session_id: Benchmark session ID
            tool_name: Tool name

        Returns:
            Full path to the tool's worktree
        """
        return self.base_path / self.worktree.base_dir / f"session-{session_id}" / tool_name

    def is_mcp_enabled(self, tool_name: str) -> bool:
        """Check if a tool is configured for MCP server usage.

        Args:
            tool_name: Tool name to check

        Returns:
            True if tool supports MCP server mode
        """
        tool_config = self.get_tool_config(tool_name)
        return tool_config.mcp_server if tool_config else False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance.

    Returns:
        Global settings instance
    """
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment and config files.

    Returns:
        Reloaded settings instance
    """
    global settings
    settings = Settings()
    return settings
