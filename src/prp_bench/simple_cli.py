"""Simple CLI for testing Claude Code benchmarking."""

import json
from pathlib import Path

import click

from .simple_runner import ClaudeCodeRunner


@click.command()
@click.argument("prompt_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file for results")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(prompt_file: str, output: str, verbose: bool) -> None:
    """Run Claude Code benchmark on a single prompt file.

    Example:
        prp-bench-simple prompts/simple/hello-world.prp.yaml

    """
    prompt_path = Path(prompt_file)

    click.echo("🚀 Running Claude Code benchmark")
    click.echo(f"📄 Prompt: {prompt_path.name}")

    # Check if Claude is available
    import subprocess

    try:
        subprocess.run(["claude", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        click.echo("❌ Error: Claude Code CLI not found. Please install it first.")
        click.echo("   npm install -g @anthropic-ai/claude-code")
        return

    # Claude Code with max subscription doesn't need API key

    # Run benchmark
    runner = ClaudeCodeRunner()

    try:
        result = runner.run_prompt(prompt_path)

        # Display results
        click.echo(
            f"\n✅ Execution completed in {result['duration_seconds']:.1f} seconds",
        )

        if verbose or not result["success"]:
            click.echo("\nOutput:")
            click.echo("-" * 40)
            click.echo(
                result["output"][:500] + "..."
                if len(result["output"]) > 500
                else result["output"],
            )

            if result.get("error"):
                click.echo("\nError:")
                click.echo("-" * 40)
                click.echo(result["error"])

        # Show file changes
        analysis = result.get("analysis", {})
        if analysis.get("files_created"):
            click.echo(f"\n📁 Files created: {len(analysis['files_created'])}")
            for f in analysis["files_created"][:5]:
                click.echo(f"   + {f}")

        if analysis.get("files_modified"):
            click.echo(f"\n✏️  Files modified: {len(analysis['files_modified'])}")
            for f in analysis["files_modified"][:5]:
                click.echo(f"   ~ {f}")

        # Save results
        if output:
            with Path(output).open("w") as f:
                json.dump(result, f, indent=2)
            click.echo(f"\n💾 Results saved to: {output}")

    except Exception as e:
        click.echo(f"\n❌ Error: {e}")
        if verbose:
            import traceback

            traceback.print_exc()


def main() -> None:
    """Main entry point."""
    run()


if __name__ == "__main__":
    main()
