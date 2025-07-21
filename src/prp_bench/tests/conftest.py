"""Pytest fixtures for PRP-Bench tests."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from prp_bench.config import LLMConfig, Settings
from prp_bench.models import ComplexityLevel, LLMExtractionResult, Prompt, PromptType


@pytest.fixture
def settings():
    """Test settings with LLM enabled."""
    return Settings(
        llm=LLMConfig(
            enabled=True,
            model="claude-3-5-haiku-20241022",
            timeout_seconds=30,
            confidence_threshold=0.6,
            fallback_enabled=True,
        )
    )


@pytest.fixture
def settings_llm_disabled():
    """Test settings with LLM disabled."""
    return Settings(
        llm=LLMConfig(
            enabled=False,
            model="claude-3-5-haiku-20241022",
            timeout_seconds=30,
            confidence_threshold=0.6,
            fallback_enabled=True,
        )
    )


@pytest.fixture
def mock_claude_sdk(mocker):
    """Mock Claude Code SDK for testing."""
    mock_query = mocker.patch("claude_code_sdk.query")
    mock_query.return_value = AsyncMock()
    return mock_query


@pytest.fixture
def high_confidence_extraction():
    """Sample high-confidence LLM extraction result."""
    return LLMExtractionResult(
        task_type="feature",
        complexity="simple",
        estimated_duration="5m",
        suggested_name="Create Hello World",
        suggested_description="Simple greeting function",
        tags=["python", "simple"],
        confidence_score=0.9,
        needs_human_review=False,
    )


@pytest.fixture
def low_confidence_extraction():
    """Sample low-confidence LLM extraction result."""
    return LLMExtractionResult(
        task_type="feature",
        complexity="simple",
        estimated_duration="5m",
        suggested_name="Unclear task",
        suggested_description="Unable to determine clear requirements",
        tags=[],
        confidence_score=0.3,
        needs_human_review=True,
    )


@pytest.fixture
def sample_yaml_content():
    """Sample YAML prompt content."""
    return """name: "Test: Simple Function"
description: "Create a simple Python function"
type: "feature"
complexity: "simple"
tags: ["test", "python"]

meta:
  expected_duration: "2m"
  validation_required: true

prompt: |
  Create a Python function that adds two numbers together.
  Include a docstring and simple test.
"""


@pytest.fixture
def sample_markdown_content():
    """Sample Markdown prompt content."""
    return """# Create Hello World

Create a simple Python script that prints "Hello, World!" to the console.
Save it as `hello.py`.
"""


@pytest.fixture
def temp_yaml_file(sample_yaml_content):
    """Temporary YAML prompt file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".prp.yaml", delete=False) as f:
        f.write(sample_yaml_content)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()


@pytest.fixture
def temp_markdown_file(sample_markdown_content):
    """Temporary Markdown prompt file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(sample_markdown_content)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()


@pytest.fixture
def temp_text_file():
    """Temporary text prompt file."""
    content = "Fix the login bug that prevents users from authenticating"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()


@pytest.fixture
def sample_prompt():
    """Sample prompt object for testing."""
    return Prompt(
        name="Test Prompt",
        description="A test prompt",
        type=PromptType.FEATURE,
        complexity=ComplexityLevel.SIMPLE,
        tags=["test"],
        prompt="Create a simple test function",
        extracted_by_llm=False,
    )
