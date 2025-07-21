"""Result formatting and output utilities for PRP-Bench."""

from typing import Any

import click

from ..models import BenchmarkRun, ToolExecutionResult


class ResultFormatter:
    """Formats benchmark results for console and file output."""

    def __init__(self, verbose: bool = False):
        """Initialize result formatter.

        Args:
            verbose: Enable verbose output mode
        """
        self.verbose = verbose

    def display_session_created(self, session_id: str) -> None:
        """Display session creation message.

        Args:
            session_id: Created session ID
        """
        click.echo(f"📋 Created session: {session_id}")

    def display_tool_starting(self, tool_name: str, timeout: int) -> None:
        """Display tool execution start message.

        Args:
            tool_name: Name of the tool being executed
            timeout: Timeout in seconds
        """
        click.echo(f"🤖 Running {tool_name.upper()} via SDK... (timeout: {timeout}s)")

    def display_tool_success(
        self, tool_name: str, duration: float, file_changes: list[Any] | None = None
    ) -> None:
        """Display tool execution success message.

        Args:
            tool_name: Name of the tool that succeeded
            duration: Execution duration in seconds
            file_changes: List of file changes (optional)
        """
        click.echo(f"✅ {tool_name.upper()} completed in {duration:.1f} seconds")

        if self.verbose and file_changes:
            created_count = len([f for f in file_changes if f.action == "created"])
            modified_count = len([f for f in file_changes if f.action == "modified"])
            click.echo(f"   Files created: {created_count}")
            click.echo(f"   Files modified: {modified_count}")

    def display_tool_failure(self, tool_name: str, error: str, stderr: str | None = None) -> None:
        """Display tool execution failure message.

        Args:
            tool_name: Name of the tool that failed
            error: Error message
            stderr: Standard error output (optional)
        """
        click.echo(f"❌ {tool_name.upper()} failed: {error}")
        if self.verbose and stderr:
            click.echo(f"   Error: {stderr}")

    def display_comparison(self, results: list[ToolExecutionResult]) -> None:
        """Display comparison of multiple tool results.

        Args:
            results: List of tool execution results
        """
        if len(results) < 2:
            return

        click.echo("\n📊 Comparison:")

        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        if successful:
            click.echo(f"   ✅ Successful: {len(successful)}/{len(results)}")

            # Show timing comparison for successful runs
            if len(successful) > 1:
                times = [(r.tool.value, r.timing.execution_duration_seconds) for r in successful]
                times.sort(key=lambda x: x[1])  # Sort by duration
                click.echo("   ⏱️  Timing:")
                for tool, duration in times:
                    click.echo(f"     {tool}: {duration:.1f}s")

        if failed:
            click.echo(f"   ❌ Failed: {len(failed)}/{len(results)}")

        # Show file changes comparison if verbose
        if self.verbose and successful:
            file_counts = {}
            for result in successful:
                if result.file_changes:
                    created = len([f for f in result.file_changes if f.action == "created"])
                    modified = len([f for f in result.file_changes if f.action == "modified"])
                    file_counts[result.tool.value] = {"created": created, "modified": modified}

            if file_counts:
                click.echo("   📁 File changes:")
                for tool, counts in file_counts.items():
                    click.echo(
                        f"     {tool}: {counts['created']} created, {counts['modified']} modified"
                    )

    def display_session_complete(self, benchmark_run: BenchmarkRun, cleanup: bool = False) -> None:
        """Display session completion information.

        Args:
            benchmark_run: Completed benchmark run
            cleanup: Whether cleanup was requested
        """
        click.echo(f"\n✅ Benchmark completed: {benchmark_run.run_id}")
        click.echo(f"📈 Results: {len(benchmark_run.results)} tools executed")

        if not cleanup:
            click.echo("🔍 Worktrees preserved for inspection")
        else:
            click.echo("🧹 Worktrees cleaned up")

    def display_worktree_locations(self, session_id: str, worktree_paths: dict[str, str]) -> None:
        """Display worktree file locations for inspection.

        Args:
            session_id: Session ID
            worktree_paths: Mapping of tool names to worktree paths
        """
        click.echo(f"\n🔍 Worktree locations for session {session_id}:")
        for tool_name, path in worktree_paths.items():
            from pathlib import Path

            if Path(path).exists():
                click.echo(f"   {tool_name}: {path}")
        click.echo(f"\\nUse 'prp-bench-cleanup {session_id}' to clean up")

    def display_error(self, message: str, verbose_error: Exception | None = None) -> None:
        """Display error message.

        Args:
            message: Error message to display
            verbose_error: Exception details for verbose mode
        """
        click.echo(f"❌ {message}")
        if self.verbose and verbose_error:
            import traceback

            traceback.print_exc()

    def display_telemetry_status(self, enabled: bool) -> None:
        """Display telemetry collection status.

        Args:
            enabled: Whether telemetry is enabled
        """
        if enabled:
            click.echo("📊 OpenTelemetry collection enabled")

    def display_cleanup_warning(self) -> None:
        """Display cleanup warning message."""
        click.echo("🔍 Worktree will be kept for inspection (use --cleanup to remove)")

    def display_llm_extraction(self, confidence: float) -> None:
        """Display LLM metadata extraction information.

        Args:
            confidence: Confidence score of LLM extraction
        """
        click.echo(f"🧠 LLM extracted metadata (confidence: {confidence:.2f})")
