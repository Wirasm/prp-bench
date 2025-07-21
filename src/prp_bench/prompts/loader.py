"""Prompt file loading functionality."""

from pathlib import Path

from ..models import Prompt
from .llm_loader import LLMPromptLoader


def load_prompt(file_path: Path) -> Prompt:
    """Load a prompt from file using LLM-powered loader.

    Args:
        file_path: Path to prompt file

    Returns:
        Prompt object (never fails)
    """
    llm_loader = LLMPromptLoader()
    return llm_loader.load_from_file(file_path)


def load_prompts_from_directory(directory: Path) -> list[Prompt]:
    """Load all prompts from a directory using LLM-powered loader.

    Args:
        directory: Directory containing prompt files

    Returns:
        List of loaded prompts (never fails - all files become valid prompts)

    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")

    llm_loader = LLMPromptLoader()
    prompts = []

    # Load all supported file types - LLM loader handles all formats gracefully
    for pattern in ["*.yaml", "*.yml", "*.md", "*.txt"]:
        for file_path in directory.glob(pattern):
            prompt = llm_loader.load_from_file(file_path)  # Never fails
            prompts.append(prompt)

    return prompts


def discover_prompt_files(base_path: Path) -> dict[str, list[Path]]:
    """Discover prompt files organized by category.

    Args:
        base_path: Base directory to search

    Returns:
        Dictionary mapping categories to prompt file lists
    """
    categories: dict[str, list[Path]] = {}

    if not base_path.exists():
        return categories

    for category_dir in base_path.iterdir():
        if not category_dir.is_dir():
            continue

        category_name = category_dir.name
        prompt_files: list[Path] = []

        # Find all prompt files in category
        for pattern in ["*.yaml", "*.yml", "*.md", "*.txt"]:
            prompt_files.extend(category_dir.glob(pattern))

        if prompt_files:
            categories[category_name] = sorted(prompt_files)

    return categories
