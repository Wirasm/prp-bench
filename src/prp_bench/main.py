"""Multi-tool CLI using Claude Code SDK orchestration."""

from pathlib import Path

import click

from .config import get_settings
from .execution import Orchestrator, SessionManager
from .prompts.loader import load_prompt


def _perform_global_cleanup() -> None:
    """Perform global cleanup of all worktrees and sessions."""
    import subprocess

    click.echo("🧹 Starting global cleanup...")

    settings = get_settings()
    Orchestrator()
    session_manager = SessionManager()

    # Get all worktrees
    try:
        result = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=settings.base_path,
            capture_output=True,
            text=True,
            check=True,
        )

        worktrees_cleaned = 0
        sessions_cleaned = 0

        # Parse worktree list and remove benchmark worktrees
        lines = result.stdout.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("worktree "):
                worktree_path = line.split("worktree ")[1]
                # Look ahead for branch info
                branch_line = ""
                if i + 2 < len(lines) and lines[i + 2].startswith("branch "):
                    branch_line = lines[i + 2]

                # Check if this is a benchmark worktree
                if "benchmark/" in branch_line:
                    try:
                        subprocess.run(
                            ["git", "worktree", "remove", worktree_path, "--force"],
                            cwd=settings.base_path,
                            capture_output=True,
                            check=False,
                        )
                        worktrees_cleaned += 1
                        click.echo(f"   ✅ Removed worktree: {Path(worktree_path).name}")
                    except Exception as e:
                        click.echo(f"   ⚠️ Failed to remove worktree {worktree_path}: {e}")
            i += 1

        # Clean up session files
        if session_manager.sessions_dir.exists():
            for session_file in session_manager.sessions_dir.glob("*.json"):
                try:
                    if "_results" in session_file.name:
                        continue  # Keep results files
                    session_id = session_file.stem
                    session_manager.cleanup_session(session_id)
                    sessions_cleaned += 1
                    click.echo(f"   ✅ Cleaned session: {session_id}")
                except Exception as e:
                    click.echo(f"   ⚠️ Failed to clean session {session_file.stem}: {e}")

        # Remove tmp/trees directory if empty
        trees_dir = settings.base_path / settings.worktree.base_dir
        if trees_dir.exists():
            try:
                # Remove empty session directories
                for session_dir in trees_dir.iterdir():
                    if session_dir.is_dir() and not any(session_dir.iterdir()):
                        session_dir.rmdir()
                        click.echo(f"   ✅ Removed empty session dir: {session_dir.name}")

                # Remove trees dir if now empty
                if not any(trees_dir.iterdir()):
                    trees_dir.rmdir()
                    click.echo("   ✅ Removed empty trees directory")
            except Exception as e:
                click.echo(f"   ⚠️ Error cleaning directories: {e}")

        # Prune git worktree references
        subprocess.run(
            ["git", "worktree", "prune"], cwd=settings.base_path, capture_output=True, check=False
        )

        click.echo("🎉 Global cleanup completed!")
        click.echo(f"   📁 Worktrees cleaned: {worktrees_cleaned}")
        click.echo(f"   📋 Sessions cleaned: {sessions_cleaned}")

    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Git worktree command failed: {e}")
    except Exception as e:
        click.echo(f"❌ Global cleanup failed: {e}")


@click.command()
@click.argument("prompt_file", type=click.Path(exists=True), required=False)
@click.option("--prompt", "-p", help="Direct prompt text (alternative to file)", type=str)
@click.option(
    "--tool",
    "-t",
    type=click.Choice(["claude", "gemini", "both"]),
    default="both",
    help="Which tool(s) to run",
)
@click.option("--output", "-o", type=click.Path(), help="Output file for results")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--timeout",
    type=int,
    help="Timeout in seconds (default: Claude=300, Gemini=600)",
)
@click.option(
    "--cleanup",
    is_flag=True,
    help="Clean up worktrees after completion, or clean all worktrees if used alone",
)
@click.option(
    "--telemetry/--no-telemetry", default=True, help="Enable/disable telemetry collection"
)
def run_sdk(
    prompt_file: str,
    prompt: str,
    tool: str,
    output: str,
    verbose: bool,
    timeout: int,
    cleanup: bool,
    telemetry: bool,
) -> None:
    """Run benchmarks using Claude Code SDK orchestration.

    This is the new SDK-powered version that uses Claude Code SDK for
    worktree management, telemetry collection, and execution.

    Examples:
        prp-bench prompts/test/hello.md
        prp-bench --prompt "Create a simple REST API endpoint"
        prp-bench prompts/test/hello.md --tool claude --telemetry
        prp-bench --prompt "Fix the login bug" --tool gemini -v --cleanup
        prp-bench --cleanup  # Clean up all worktrees and sessions

    """
    # Special case: cleanup-only mode
    if cleanup and not prompt_file and not prompt:
        # Global cleanup mode - clean all worktrees and sessions
        _perform_global_cleanup()
        return

    # Validate input - need either file or prompt text
    if not prompt_file and not prompt:
        click.echo("❌ Error: Must provide either a prompt file or --prompt text")
        return

    if prompt_file and prompt:
        click.echo("❌ Error: Cannot specify both prompt file and --prompt text")
        return

    settings = get_settings()

    # Override telemetry setting
    settings.telemetry.enabled = telemetry

    # Load prompt - either from file or direct text
    try:
        if prompt_file:
            prompt_obj = load_prompt(Path(prompt_file))
            prompt_source = Path(prompt_file).name
        else:
            # Create prompt from string using LLM loader
            from .prompts.llm_loader import LLMPromptLoader

            llm_loader = LLMPromptLoader()
            prompt_obj = llm_loader.load_from_string(prompt)
            prompt_source = "direct input"

            # Show LLM extraction info if metadata was extracted
            if prompt_obj.extracted_by_llm:
                click.echo(
                    f"🧠 LLM extracted metadata (confidence: {prompt_obj.extraction_confidence:.2f})"
                )

    except Exception as e:
        click.echo(f"❌ Failed to load prompt: {e}")
        return

    # Determine which tools to run
    tools_to_run = []
    if tool in ["claude", "both"]:
        tools_to_run.append("claude")
    if tool in ["gemini", "both"]:
        tools_to_run.append("gemini")

    click.echo(f"🚀 Running SDK-powered benchmark with: {', '.join(tools_to_run)}")
    click.echo(f"📄 Prompt: {prompt_source}")

    if not cleanup:
        click.echo("🔍 Worktree will be kept for inspection (use --cleanup to remove)")

    if telemetry:
        click.echo("📊 OpenTelemetry collection enabled")

    click.echo()

    # Initialize SDK components
    orchestrator = Orchestrator(base_path=settings.base_path, enable_telemetry=telemetry)
    session_manager = SessionManager(base_path=settings.base_path)

    try:
        # Create benchmark session
        session = session_manager.create_session(
            prompt=prompt_obj, tools=tools_to_run, telemetry_enabled=telemetry
        )

        click.echo(f"📋 Created session: {session.session_id}")

        # Use the session ID consistently across both systems
        session_id = session.session_id

        # Create isolated worktrees via SDK using our session ID
        orchestrator.create_benchmark_session_with_id(session_id, prompt_obj, tools_to_run)
        session_manager.update_session_status(session_id, "running")

        results = []

        # Execute each tool using SDK orchestration
        for tool_name in tools_to_run:
            tool_config = settings.get_tool_config(tool_name)
            # Handle case where tool_config might be None
            default_timeout = tool_config.default_timeout if tool_config else 300
            tool_timeout = timeout or default_timeout

            click.echo(f"🤖 Running {tool_name.upper()} via SDK... (timeout: {tool_timeout}s)")

            try:
                # Execute via SDK with proper isolation and telemetry
                result = orchestrator.execute_tool_via_sdk(
                    session_id=session_id,
                    tool=tool_name,
                    prompt=prompt_obj,
                    timeout_seconds=tool_timeout,
                )

                results.append(result)
                session_manager.add_result(session_id, result)

                # Store worktree path for inspection
                worktree_path = settings.get_worktree_path(session_id, tool_name)
                session_manager.set_worktree_path(session_id, tool_name, str(worktree_path))

                if result.success:
                    duration = result.timing.execution_duration_seconds
                    click.echo(f"✅ {tool_name.upper()} completed in {duration:.1f} seconds")

                    if verbose and result.file_changes:
                        click.echo(
                            f"   Files created: {len([f for f in result.file_changes if f.action == 'created'])}"
                        )
                        click.echo(
                            f"   Files modified: {len([f for f in result.file_changes if f.action == 'modified'])}"
                        )
                else:
                    click.echo(f"❌ {tool_name.upper()} failed: {result.error}")
                    if verbose and result.stderr:
                        click.echo(f"   Error: {result.stderr}")

            except Exception as e:
                click.echo(f"❌ {tool_name.upper()} error: {e}")
                if verbose:
                    import traceback

                    traceback.print_exc()

        # Display comparison if multiple tools
        if len(results) > 1:
            _display_comparison(results, verbose)

        # Complete session and generate final report
        benchmark_run = session_manager.complete_session(session_id)

        # Save results if output specified
        if output and results:
            output_path = Path(output)

            if len(results) == 1:
                # Single tool result
                with output_path.open("w") as f:
                    f.write(results[0].model_dump_json(indent=2))
            else:
                # Multiple tools - save full benchmark run
                with output_path.open("w") as f:
                    f.write(benchmark_run.model_dump_json(indent=2))

            click.echo(f"\n💾 Results saved to: {output}")

        # Show session info for inspection
        if not cleanup:
            click.echo(f"\n🔍 Session {session_id} preserved for inspection:")
            for tool_name in tools_to_run:
                worktree_path = settings.get_worktree_path(session_id, tool_name)
                if worktree_path.exists():
                    click.echo(f"   {tool_name}: {worktree_path}")
            click.echo(f"\nUse 'prp-bench-cleanup {session_id}' to clean up")

    except Exception as e:
        click.echo(f"❌ Benchmark failed: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        return

    finally:
        # Cleanup if requested
        if cleanup:
            try:
                orchestrator.cleanup_session(session_id)
                session_manager.cleanup_session(session_id)
                click.echo("🧹 Session cleaned up")
            except Exception as e:
                click.echo(f"⚠️ Cleanup warning: {e}")


def _display_comparison(results: list, verbose: bool) -> None:
    """Display comparison between tool results."""
    if len(results) < 2:
        return

    click.echo("\n📊 Comparison:")

    # Performance comparison
    for result in results:
        duration = result.timing.execution_duration_seconds
        status = "✅" if result.success else "❌"
        click.echo(f"   {result.tool.value}: {status} {duration:.1f}s")

    # Success comparison
    successful = [r for r in results if r.success]
    if successful:
        # Compare file changes
        file_counts = {}
        for result in successful:
            created = len([f for f in result.file_changes if f.action == "created"])
            modified = len([f for f in result.file_changes if f.action == "modified"])
            file_counts[result.tool.value] = {"created": created, "modified": modified}

        if file_counts and verbose:
            click.echo("   File changes:")
            for tool, counts in file_counts.items():
                click.echo(
                    f"     {tool}: {counts['created']} created, {counts['modified']} modified"
                )


def main_sdk() -> None:
    """Main entry point for SDK-powered multi-tool benchmarking."""
    run_sdk()


if __name__ == "__main__":
    main_sdk()
