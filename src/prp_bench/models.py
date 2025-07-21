"""Data models for PRP-Bench."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ToolType(str, Enum):
    """Supported AI coding CLI tools."""

    CLAUDE_CODE = "claude"
    GEMINI = "gemini"
    CODEX = "codex"


class PromptType(str, Enum):
    """Types of prompts."""

    FEATURE = "feature"
    BUG = "bug"
    REFACTOR = "refactor"
    TEST = "test"
    DOCS = "docs"


class ComplexityLevel(str, Enum):
    """Prompt complexity levels."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class ValidationCommand(BaseModel):
    """A validation command to run."""

    description: str | None = None
    command: str
    expected: str | None = None
    timeout: int = Field(default=60, description="Timeout in seconds")


class PromptContext(BaseModel):
    """Context for a prompt."""

    files: list[dict[str, str]] = Field(default_factory=list)
    urls: list[dict[str, str]] = Field(default_factory=list)


class PromptValidation(BaseModel):
    """Validation configuration for a prompt."""

    syntax: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    integration: list[ValidationCommand] = Field(default_factory=list)


class ExpectedOutcomes(BaseModel):
    """Expected outcomes from prompt execution."""

    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)


class PromptMetadata(BaseModel):
    """Metadata for benchmarking."""

    expected_duration: str | None = None
    expected_loc: int | None = None
    validation_required: bool = True


class Prompt(BaseModel):
    """A prompt to execute."""

    prompt_id: UUID = Field(default_factory=uuid4)
    name: str
    description: str
    type: PromptType
    complexity: ComplexityLevel
    tags: list[str] = Field(default_factory=list)
    meta: PromptMetadata
    prompt: str
    context: PromptContext | None = None
    validation: PromptValidation | None = None
    expected_outcomes: ExpectedOutcomes | None = None
    source_file: Path | None = None


class ResourceMetrics(BaseModel):
    """Resource usage metrics."""

    peak_cpu_percent: float
    peak_memory_mb: float
    disk_usage_mb: float
    network_requests: int = 0


class TokenUsage(BaseModel):
    """Token usage statistics."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    total_tokens: int = 0


class ExecutionTiming(BaseModel):
    """Timing information for execution."""

    start_time: datetime
    end_time: datetime | None = None
    setup_duration_seconds: float = 0.0
    execution_duration_seconds: float = 0.0
    validation_duration_seconds: float = 0.0
    total_duration_seconds: float = 0.0


class ValidationResult(BaseModel):
    """Result of a validation command."""

    command: str
    success: bool
    output: str
    error: str | None = None
    duration_seconds: float


class FileChange(BaseModel):
    """A file change made by the tool."""

    path: str
    action: str  # created, modified, deleted
    lines_added: int = 0
    lines_removed: int = 0


class ToolExecutionResult(BaseModel):
    """Result of executing a tool on a prompt."""

    tool: ToolType
    prompt_id: UUID
    run_id: UUID = Field(default_factory=uuid4)
    success: bool

    # Execution details
    timing: ExecutionTiming
    token_usage: TokenUsage | None = None
    estimated_cost: Decimal | None = None
    resource_metrics: ResourceMetrics | None = None

    # Output
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None

    # Changes made
    file_changes: list[FileChange] = Field(default_factory=list)
    git_diff: str | None = None

    # Validation
    validation_results: list[ValidationResult] = Field(default_factory=list)
    all_validations_passed: bool = False

    # Errors
    error: str | None = None
    error_type: str | None = None


class BenchmarkRun(BaseModel):
    """A complete benchmark run."""

    run_id: UUID = Field(default_factory=uuid4)
    started_at: datetime = Field(default_factory=lambda: datetime.now())
    completed_at: datetime | None = None

    # Configuration
    tools: list[ToolType]
    prompts: list[Prompt]
    parallel: bool = False

    # Results
    results: list[ToolExecutionResult] = Field(default_factory=list)

    # Summary statistics
    total_prompts: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0

    def add_result(self, result: ToolExecutionResult) -> None:
        """Add a result to the benchmark run."""
        self.results.append(result)
        self.total_executions += 1
        if result.success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1


class ToolConfig(BaseModel):
    """Configuration for a specific tool."""

    tool: ToolType
    executable: str
    api_key_env: str
    auto_approve_flag: str
    additional_flags: list[str] = Field(default_factory=list)
    environment: dict[str, str] = Field(default_factory=dict)


# Tool configurations based on research
TOOL_CONFIGS = {
    ToolType.CLAUDE_CODE: ToolConfig(
        tool=ToolType.CLAUDE_CODE,
        executable="claude",
        api_key_env="ANTHROPIC_API_KEY",
        auto_approve_flag="--dangerously-skip-permissions",
        additional_flags=["-p"],
        environment={
            "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
            "OTEL_METRICS_EXPORTER": "otlp",
            "OTEL_LOGS_EXPORTER": "otlp",
            "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317",
        },
    ),
    ToolType.GEMINI: ToolConfig(
        tool=ToolType.GEMINI,
        executable="gemini",
        api_key_env="GEMINI_API_KEY",
        auto_approve_flag="--yolo",
        additional_flags=[],
        environment={},
    ),
    ToolType.CODEX: ToolConfig(
        tool=ToolType.CODEX,
        executable="codex",
        api_key_env="OPENAI_API_KEY",
        auto_approve_flag="--dangerously-auto-approve-everything",
        additional_flags=["exec"],
        environment={},
    ),
}
