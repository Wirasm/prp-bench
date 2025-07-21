"""Main CLI entry point for PRP-Bench."""

import asyncio
from pathlib import Path

import click
import yaml
from anthropic import Anthropic

from .models import ComplexityLevel, Prompt, PromptMetadata, PromptType
from .runner import BenchmarkRunner


def load_prompt_file(file_path: Path) -> Prompt:
    """Load a prompt from file.

    Args:
        file_path: Path to prompt file

    Returns:
        Prompt object

    """
    if file_path.suffix in [".yaml", ".yml"]:
        with file_path.open() as f:
            data = yaml.safe_load(f)

        # Convert to Prompt object
        prompt = Prompt(
            name=data["name"],
            description=data["description"],
            type=PromptType(data["type"]),
            complexity=ComplexityLevel(data["complexity"]),
            tags=data.get("tags", []),
            meta=PromptMetadata(**data.get("meta", {})),
            prompt=data["prompt"],
            source_file=file_path,
        )
    else:
        # Plain text/markdown file
        content = file_path.read_text()

        # Simple parsing - first line as name
        lines = content.strip().split("\n")
        name = lines[0].strip("# ").strip()

        prompt = Prompt(
            name=name,
            description=name,
            type=PromptType.FEATURE,
            complexity=ComplexityLevel.MEDIUM,
            meta=PromptMetadata(),
            prompt=content,
            source_file=file_path,
        )

    return prompt


@click.command()
@click.argument("prompt_files", nargs=-1, type=click.Path(exists=True))
@click.option(
    "--tools",
    "-t",
    multiple=True,
    default=["claude", "gemini", "codex"],
    help="Tools to benchmark",
)
@click.option("--output", "-o", type=click.Path(), help="Output file for results")
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", help="Anthropic API key")
def run(prompt_files: list[str], tools: list[str], output: str | None, api_key: str) -> None:
    """Run PRP-Bench on the specified prompt files.

    Examples:
        prp-bench prompts/simple/fix-bug.prp.yaml
        prp-bench prompts/medium/*.yaml --tools claude,gemini
        prp-bench prompts/complex/refactor.md -o results.json

    """
    if not prompt_files:
        click.echo("Error: No prompt files specified")
        return

    if not api_key:
        click.echo("Error: ANTHROPIC_API_KEY not set")
        return

    # Load prompts
    prompts = []
    for file_path in prompt_files:
        path = Path(file_path)
        if path.is_file():
            prompt = load_prompt_file(path)
            prompts.append(prompt)
            click.echo(f"Loaded prompt: {prompt.name}")

    if not prompts:
        click.echo("Error: No valid prompts found")
        return

    # Initialize runner
    client = Anthropic(api_key=api_key)
    runner = BenchmarkRunner(client)

    # Run benchmark
    click.echo(f"\nRunning benchmark with tools: {', '.join(tools)}")
    click.echo(f"Total prompts: {len(prompts)}\n")

    # Run async function
    results = asyncio.run(runner.run_benchmark(prompts, list(tools)))

    # Display results
    click.echo("\nResults:")
    click.echo(f"Total executions: {results.total_executions}")
    click.echo(f"Successful: {results.successful_executions}")
    click.echo(f"Failed: {results.failed_executions}")

    # Save results if output specified
    if output:
        output_path = Path(output)
        with output_path.open("w") as f:
            f.write(results.model_dump_json(indent=2))
        click.echo(f"\nResults saved to: {output}")


def main() -> None:
    """Main entry point."""
    run()


if __name__ == "__main__":
    main()
