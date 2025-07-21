"""Multi-tool CLI for benchmarking Claude and Gemini."""

import json
from pathlib import Path

import click

from .gemini_runner import GeminiRunner
from .simple_runner import ClaudeCodeRunner


@click.command()
@click.argument("prompt_file", type=click.Path(exists=True))
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
    "--timeout", type=int, help="Timeout in seconds (default: Claude=300, Gemini=600)",
)
@click.option(
    "--cleanup", is_flag=True, help="Clean up worktree after completion"
)
def run(prompt_file: str, tool: str, output: str, verbose: bool, timeout: int, cleanup: bool) -> None:
    """Run benchmarks on Claude and/or Gemini.

    Examples:
        prp-bench-multi prompts/test/hello.md
        prp-bench-multi prompts/test/hello.md --tool claude
        prp-bench-multi prompts/test/hello.md --tool gemini -v

    """
    prompt_path = Path(prompt_file)
    results = []

    # Determine which tools to run
    tools_to_run = []
    if tool in ["claude", "both"]:
        tools_to_run.append("claude")
    if tool in ["gemini", "both"]:
        tools_to_run.append("gemini")

    click.echo(f"🚀 Running benchmark with: {', '.join(tools_to_run)}")
    click.echo(f"📄 Prompt: {prompt_path.name}")
    if not cleanup:
        click.echo("🔍 Worktree will be kept for inspection (use --cleanup to remove)")
    click.echo()

    # Run Claude if requested
    if "claude" in tools_to_run:
        # Check if Claude is available
        import subprocess

        try:
            subprocess.run(["claude", "--version"], capture_output=True, check=True)
            # Use custom timeout or default to 300 seconds for Claude
            claude_timeout = timeout if timeout else 300
            click.echo(f"🤖 Running Claude Code... (timeout: {claude_timeout}s)")
            runner = ClaudeCodeRunner(timeout_seconds=claude_timeout)
            try:
                result = runner.run_prompt(prompt_path, cleanup=cleanup)
                results.append(result)

                click.echo(
                    f"✅ Claude completed in {result['duration_seconds']:.1f} seconds",
                )
                if verbose:
                    click.echo(
                        f"   Files created: {len(result['analysis'].get('files_created', []))}",
                    )
                    click.echo(
                        f"   Files modified: {len(result['analysis'].get('files_modified', []))}",
                    )

            except Exception as e:
                click.echo(f"❌ Claude error: {e}")
                if verbose:
                    import traceback

                    traceback.print_exc()

        except (subprocess.CalledProcessError, FileNotFoundError):
            click.echo("⚠️  Claude Code CLI not found. Skipping...")

    # Run Gemini if requested
    if "gemini" in tools_to_run:
        # Check if Gemini is available
        import subprocess

        try:
            subprocess.run(["gemini", "--version"], capture_output=True, check=True)
            # Use custom timeout or default to 600 seconds for Gemini
            gemini_timeout = timeout if timeout else 600
            click.echo(f"\n🌟 Running Gemini CLI... (timeout: {gemini_timeout}s)")
            gemini_runner = GeminiRunner(timeout_seconds=gemini_timeout)
            try:
                result = gemini_runner.run_prompt(prompt_path, cleanup=cleanup)
                results.append(result)

                click.echo(
                    f"✅ Gemini completed in {result['duration_seconds']:.1f} seconds",
                )
                if verbose:
                    click.echo(
                        f"   Files created: {len(result['analysis'].get('files_created', []))}",
                    )
                    click.echo(
                        f"   Files modified: {len(result['analysis'].get('files_modified', []))}",
                    )

            except Exception as e:
                click.echo(f"❌ Gemini error: {e}")
                if verbose:
                    import traceback

                    traceback.print_exc()

        except (subprocess.CalledProcessError, FileNotFoundError):
            click.echo("⚠️  Gemini CLI not found. Skipping...")

    # Display comparison if both tools were run
    if len(results) == 2:
        click.echo("\n📊 Comparison:")
        click.echo(f"   Claude: {results[0]['duration_seconds']:.1f}s")
        click.echo(f"   Gemini: {results[1]['duration_seconds']:.1f}s")

        # Compare files created
        claude_files = set(results[0]["analysis"].get("files_created", []))
        gemini_files = set(results[1]["analysis"].get("files_created", []))

        if claude_files == gemini_files:
            click.echo(f"   Both created the same {len(claude_files)} files")
        else:
            click.echo(f"   Claude created: {claude_files}")
            click.echo(f"   Gemini created: {gemini_files}")

    # Save results if output specified
    if output and results:
        with Path(output).open("w") as f:
            if len(results) == 1:
                json.dump(results[0], f, indent=2)
            else:
                json.dump({"results": results}, f, indent=2)
        click.echo(f"\n💾 Results saved to: {output}")


def main() -> None:
    """Main entry point."""
    run()


@click.command()
@click.option("--all", is_flag=True, help="Clean up all worktrees in tmp/trees")
@click.argument("run_id", required=False)
def cleanup(all: bool, run_id: str | None) -> None:
    """Clean up benchmark worktrees.
    
    Examples:
        prp-bench-cleanup --all
        prp-bench-cleanup abc12345
    """
    import shutil
    import subprocess
    
    base_path = Path.cwd()
    tmp_dir = base_path / "tmp" / "trees"
    
    if not tmp_dir.exists():
        click.echo("No tmp/trees directory found")
        return
    
    if all:
        click.echo("🧹 Cleaning up all worktrees...")
        try:
            # Remove all worktrees
            subprocess.run(
                ["git", "worktree", "prune"], 
                cwd=base_path, 
                capture_output=True, 
                check=False
            )
            # Remove directory
            if tmp_dir.exists():
                shutil.rmtree(tmp_dir)
            click.echo("✅ All worktrees cleaned up")
        except Exception as e:
            click.echo(f"❌ Error cleaning up: {e}")
    elif run_id:
        # Clean up specific run
        claude_dir = tmp_dir / f"claude-{run_id}"
        gemini_dir = tmp_dir / f"gemini-{run_id}"
        
        cleaned = []
        for worktree_dir in [claude_dir, gemini_dir]:
            if worktree_dir.exists():
                try:
                    subprocess.run(
                        ["git", "worktree", "remove", str(worktree_dir), "--force"],
                        cwd=base_path,
                        capture_output=True,
                        check=False
                    )
                    if worktree_dir.exists():
                        shutil.rmtree(worktree_dir)
                    cleaned.append(worktree_dir.name)
                except Exception as e:
                    click.echo(f"❌ Error cleaning {worktree_dir.name}: {e}")
        
        if cleaned:
            click.echo(f"✅ Cleaned up: {', '.join(cleaned)}")
            # Prune refs
            subprocess.run(
                ["git", "worktree", "prune"], 
                cwd=base_path, 
                capture_output=True, 
                check=False
            )
        else:
            click.echo(f"No worktrees found for run ID: {run_id}")
    else:
        # List available worktrees
        if tmp_dir.exists():
            worktrees = list(tmp_dir.iterdir())
            if worktrees:
                click.echo("Available worktrees:")
                for wt in worktrees:
                    if wt.is_dir():
                        click.echo(f"  - {wt.name}")
                click.echo("\nUse --all to clean all, or specify a run ID")
            else:
                click.echo("No worktrees found in tmp/trees")
        else:
            click.echo("No tmp/trees directory found")


if __name__ == "__main__":
    main()
