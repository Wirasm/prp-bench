"""Claude Code SDK-powered orchestration for multi-tool benchmarking."""

import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from ..models import ExecutionTiming, Prompt, ToolExecutionResult, ToolType


class Orchestrator:
    """Orchestrates multi-tool benchmarks using Claude Code SDK capabilities."""

    def __init__(self, base_path: Path | None = None, enable_telemetry: bool = True):
        """Initialize orchestrator with Claude Code SDK integration.

        Args:
            base_path: Base directory for operations
            enable_telemetry: Whether to enable OpenTelemetry collection
        """
        from ..config import get_settings

        self.base_path = base_path or Path.cwd()
        self.enable_telemetry = enable_telemetry

        # Use consistent WorktreeConfig for directory structure
        settings = get_settings()
        self.tmp_dir = self.base_path / settings.worktree.base_dir
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def create_benchmark_session(self, prompt: Prompt, tools: list[str]) -> str:
        """Create isolated benchmark session using Claude Code SDK.

        Args:
            prompt: Prompt to execute across tools
            tools: List of tool names to benchmark

        Returns:
            Session ID for tracking
        """
        session_id = str(uuid4())[:8]

        # Create session directory structure
        session_dir = self.tmp_dir / f"session-{session_id}"
        session_dir.mkdir(exist_ok=True)

        # Create worktrees for each tool using SDK
        for tool in tools:
            self._create_tool_worktree(session_id, tool, prompt)

        return session_id

    def create_benchmark_session_with_id(
        self, session_id: str, prompt: Prompt, tools: list[str]
    ) -> None:
        """Create isolated benchmark session with specific session ID.

        Args:
            session_id: Specific session ID to use
            prompt: Prompt to execute across tools
            tools: List of tool names to benchmark
        """
        # Create session directory structure
        session_dir = self.tmp_dir / f"session-{session_id}"
        session_dir.mkdir(exist_ok=True)

        # Create worktrees for each tool using SDK
        for tool in tools:
            self._create_tool_worktree(session_id, tool, prompt)

    def _create_tool_worktree(self, session_id: str, tool: str, prompt: Prompt) -> Path:
        """Create isolated worktree for a specific tool using Claude Code SDK.

        Args:
            session_id: Benchmark session ID
            tool: Tool name (claude, gemini, etc.)
            prompt: Prompt to execute

        Returns:
            Path to created worktree
        """
        worktree_dir = self.tmp_dir / f"session-{session_id}" / tool

        # Use git worktree for isolation
        branch_name = f"benchmark/{tool}/{session_id}"

        try:
            # Create worktree branch
            cmd = ["git", "worktree", "add", "-b", branch_name, str(worktree_dir)]
            subprocess.run(cmd, cwd=self.base_path, check=True, capture_output=True)

            # Copy environment files
            env_file = self.base_path / ".env"
            if env_file.exists():
                import shutil

                shutil.copy2(env_file, worktree_dir / ".env")

            # Save prompt content for reference
            prompt_file = worktree_dir / "benchmark_prompt.md"
            prompt_file.write_text(prompt.prompt)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create worktree for {tool}: {e}") from e

        return worktree_dir

    def execute_tool_via_sdk(
        self, session_id: str, tool: str, prompt: Prompt, timeout_seconds: int = 300
    ) -> ToolExecutionResult:
        """Execute a tool using Claude Code SDK with proper isolation.

        Args:
            session_id: Benchmark session ID
            tool: Tool to execute
            prompt: Prompt to run
            timeout_seconds: Execution timeout

        Returns:
            Execution result with telemetry data
        """
        worktree_dir = self.tmp_dir / f"session-{session_id}" / tool
        start_time = datetime.now(UTC)

        try:
            if tool == "claude":
                result = self._execute_claude_via_sdk(worktree_dir, prompt, timeout_seconds)
            elif tool == "gemini":
                result = self._execute_gemini_via_sdk(worktree_dir, prompt, timeout_seconds)
            else:
                raise ValueError(f"Unsupported tool: {tool}")

            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            # Analyze results using git
            analysis = self._analyze_worktree_changes(worktree_dir)

            return ToolExecutionResult(
                tool=ToolType(tool),
                prompt_id=prompt.prompt_id,
                success=result.get("success", False),
                timing=self._create_timing_info(start_time, end_time, duration),
                stdout=result.get("output", ""),
                stderr=result.get("error") or "",
                file_changes=analysis.get("file_changes", []),
                git_diff=analysis.get("git_diff", ""),
            )

        except Exception as e:
            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            return ToolExecutionResult(
                tool=ToolType(tool),
                prompt_id=prompt.prompt_id,
                success=False,
                timing=self._create_timing_info(start_time, end_time, duration),
                error=str(e),
                error_type=type(e).__name__,
            )

    def _execute_claude_via_sdk(
        self, worktree_dir: Path, prompt: Prompt, timeout_seconds: int
    ) -> dict[str, Any]:
        """Execute Claude Code using SDK in non-interactive mode.

        Uses Claude Code SDK's -p flag for prompt-based execution with
        proper cwd isolation and telemetry collection.
        """
        # Use Claude Code SDK with proper flags
        cmd = ["claude", "--dangerously-skip-permissions", "-p", prompt.prompt]

        # Setup environment for telemetry if enabled
        env = self._setup_telemetry_env()

        try:
            result = subprocess.run(
                cmd,
                check=False,
                cwd=worktree_dir,  # SDK respects cwd for isolation
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=env,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Claude execution timed out after {timeout_seconds} seconds",
            }

    def _execute_gemini_via_sdk(
        self, worktree_dir: Path, prompt: Prompt, timeout_seconds: int
    ) -> dict[str, Any]:
        """Execute Gemini CLI in isolated worktree.

        Future: This will be replaced with MCP server integration.
        """
        cmd = ["gemini", "-p", prompt.prompt, "--yolo"]

        try:
            result = subprocess.run(
                cmd,
                check=False,
                cwd=worktree_dir,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Gemini execution timed out after {timeout_seconds} seconds",
            }

    def _setup_telemetry_env(self) -> dict[str, str]:
        """Setup environment variables for Claude Code SDK telemetry.

        Enables OpenTelemetry collection with proper configuration.
        """
        import os

        env = os.environ.copy()

        if self.enable_telemetry:
            env.update(
                {
                    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
                    "OTEL_METRICS_EXPORTER": "console",  # Can be changed to otlp
                    "OTEL_RESOURCE_ATTRIBUTES": "service.name=prp-bench,service.version=0.1.0",
                }
            )

        return env

    def _analyze_worktree_changes(self, worktree_dir: Path) -> dict[str, Any]:
        """Analyze what changes were made in the worktree."""
        analysis: dict[str, Any] = {
            "file_changes": [],
            "git_diff": "",
            "files_created": list[str](),
            "files_modified": list[str](),
        }

        try:
            # Get git status
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=worktree_dir,
                capture_output=True,
                text=True,
                check=False,
            )

            # Parse file changes
            for line in status.stdout.splitlines():
                if line.startswith("??"):
                    analysis["files_created"].append(line[3:])
                elif line.startswith((" M", "M ")):
                    analysis["files_modified"].append(line[3:])

            # Get diff
            diff = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=worktree_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            analysis["git_diff"] = diff.stdout

        except Exception as e:
            analysis["error"] = str(e)

        return analysis

    def _create_timing_info(
        self, start_time: datetime, end_time: datetime, duration: float
    ) -> ExecutionTiming:
        """Create timing information object."""

        return ExecutionTiming(
            start_time=start_time,
            end_time=end_time,
            execution_duration_seconds=duration,
            total_duration_seconds=duration,
        )

    def cleanup_session(self, session_id: str) -> None:
        """Clean up benchmark session worktrees.

        Args:
            session_id: Session ID to clean up
        """
        session_dir = self.tmp_dir / f"session-{session_id}"

        if not session_dir.exists():
            return

        # Clean up individual tool worktrees
        for tool_dir in session_dir.iterdir():
            if tool_dir.is_dir():
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", str(tool_dir), "--force"],
                        cwd=self.base_path,
                        capture_output=True,
                        check=False,
                    )
                except Exception:
                    # Fallback to manual removal
                    import shutil

                    if tool_dir.exists():
                        shutil.rmtree(tool_dir)

        # Clean up session directory
        if session_dir.exists():
            import shutil

            shutil.rmtree(session_dir)

        # Prune git worktree references
        subprocess.run(
            ["git", "worktree", "prune"], cwd=self.base_path, capture_output=True, check=False
        )
