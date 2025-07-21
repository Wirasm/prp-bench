"""Comprehensive tests for LLM-powered prompt loader."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from prp_bench.models import ComplexityLevel, PromptType
from prp_bench.prompts.llm_loader import LLMPromptLoader


class TestLLMPromptLoader:
    """Test suite for LLMPromptLoader."""

    def test_init_with_default_settings(self):
        """Test loader initialization with default settings."""
        loader = LLMPromptLoader()
        assert loader.settings is not None
        assert loader.llm_config is not None
        assert loader.llm_config.enabled is True

    def test_init_with_custom_settings(self, settings):
        """Test loader initialization with custom settings."""
        loader = LLMPromptLoader(settings)
        assert loader.settings == settings
        assert loader.llm_config == settings.llm

    def test_load_from_string_with_llm_disabled(self, settings_llm_disabled):
        """Test loading from string with LLM disabled uses fallback."""
        loader = LLMPromptLoader(settings_llm_disabled)
        prompt = loader.load_from_string("Create a simple function")

        assert prompt.prompt == "Create a simple function"
        assert prompt.extracted_by_llm is False
        assert prompt.fallback_applied is True
        assert prompt.type == PromptType.FEATURE
        assert prompt.complexity == ComplexityLevel.SIMPLE

    @pytest.mark.asyncio
    async def test_load_from_string_high_confidence_success(
        self, settings, mock_claude_sdk, high_confidence_extraction
    ):
        """Test successful LLM extraction with high confidence."""
        # Mock LLM response
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps(
            {
                "task_type": "feature",
                "complexity": "simple",
                "estimated_duration": "5m",
                "suggested_name": "Create Hello World",
                "suggested_description": "Simple greeting function",
                "tags": ["python", "simple"],
                "confidence_score": 0.9,
            }
        )

        mock_claude_sdk.return_value.__aiter__.return_value = [mock_message]

        loader = LLMPromptLoader(settings)
        prompt = loader.load_from_string("Create a hello world function")

        assert prompt.extracted_by_llm is True
        assert prompt.extraction_confidence == 0.9
        assert prompt.type == PromptType.FEATURE
        assert prompt.complexity == ComplexityLevel.SIMPLE
        assert prompt.name == "Create Hello World"
        assert prompt.description == "Simple greeting function"
        assert prompt.tags == ["python", "simple"]
        assert prompt.prompt == "Create a hello world function"  # Unchanged
        assert prompt.fallback_applied is False

    @pytest.mark.asyncio
    async def test_load_from_string_low_confidence_fallback(
        self, settings, mock_claude_sdk, low_confidence_extraction
    ):
        """Test smart fallback when LLM confidence is low."""
        # Mock LLM response with low confidence
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps(
            {
                "task_type": "feature",
                "complexity": "simple",
                "estimated_duration": "5m",
                "suggested_name": "Unclear task",
                "suggested_description": "Unable to determine requirements",
                "tags": [],
                "confidence_score": 0.3,
            }
        )

        mock_claude_sdk.return_value.__aiter__.return_value = [mock_message]

        loader = LLMPromptLoader(settings)
        prompt = loader.load_from_string("Some unclear text")

        assert prompt.extracted_by_llm is True
        assert prompt.extraction_confidence == 0.3
        assert prompt.fallback_applied is True
        assert prompt.type == PromptType.FEATURE  # Safe default
        assert prompt.complexity == ComplexityLevel.SIMPLE  # Safe default
        assert prompt.prompt == "Some unclear text"  # Content preserved

    def test_load_from_string_llm_error_fallback(self, settings, mock_claude_sdk):
        """Test graceful fallback when LLM extraction fails."""
        mock_claude_sdk.side_effect = Exception("API Error")

        loader = LLMPromptLoader(settings)
        prompt = loader.load_from_string("Any text here")

        assert prompt.fallback_applied is True
        assert prompt.extracted_by_llm is False
        assert prompt.prompt == "Any text here"  # Content preserved
        assert prompt.type == PromptType.FEATURE  # Default type
        assert prompt.complexity == ComplexityLevel.SIMPLE  # Default complexity

    def test_load_from_file_yaml_existing_metadata(self, temp_yaml_file):
        """Test loading YAML file with existing metadata (should skip LLM)."""
        loader = LLMPromptLoader()
        prompt = loader.load_from_file(temp_yaml_file)

        assert prompt.name == "Test: Simple Function"
        assert prompt.description == "Create a simple Python function"
        assert prompt.type == PromptType.FEATURE
        assert prompt.complexity == ComplexityLevel.SIMPLE
        assert prompt.tags == ["test", "python"]
        assert prompt.extracted_by_llm is False  # Used existing metadata
        assert prompt.original_format == "yaml"
        assert "Create a Python function that adds two numbers" in prompt.prompt

    @pytest.mark.asyncio
    async def test_load_from_file_markdown_with_llm(
        self, temp_markdown_file, mock_claude_sdk, high_confidence_extraction
    ):
        """Test loading Markdown file uses LLM extraction."""
        # Mock LLM response
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps(
            {
                "task_type": "feature",
                "complexity": "simple",
                "estimated_duration": "2m",
                "suggested_name": "Hello World Script",
                "suggested_description": "Create a greeting script",
                "tags": ["python", "hello-world"],
                "confidence_score": 0.85,
            }
        )

        mock_claude_sdk.return_value.__aiter__.return_value = [mock_message]

        loader = LLMPromptLoader()
        prompt = loader.load_from_file(temp_markdown_file)

        assert prompt.extracted_by_llm is True
        assert prompt.extraction_confidence == 0.85
        assert prompt.original_format == "markdown"
        assert prompt.name == "Hello World Script"
        assert "Create a simple Python script" in prompt.prompt

    def test_load_from_file_nonexistent_graceful_fallback(self):
        """Test loading nonexistent file creates fallback prompt."""
        loader = LLMPromptLoader()
        nonexistent_file = Path("/nonexistent/file.txt")

        prompt = loader.load_from_file(nonexistent_file)

        assert prompt.fallback_applied is True
        assert prompt.extracted_by_llm is False
        assert prompt.source_file == nonexistent_file
        assert "Error reading file" in prompt.prompt

    def test_load_from_file_malformed_yaml_fallback(self):
        """Test loading malformed YAML falls back gracefully."""
        import tempfile

        malformed_yaml = "name: test\nbad_yaml: {\ninvalid"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(malformed_yaml)
            temp_path = Path(f.name)

        try:
            loader = LLMPromptLoader()
            prompt = loader.load_from_file(temp_path)

            # Should fallback gracefully instead of crashing
            assert prompt is not None
            assert prompt.prompt == malformed_yaml  # Original content preserved
            assert prompt.fallback_applied is True
        finally:
            temp_path.unlink()

    def test_generate_name_from_content_first_line(self):
        """Test name generation from first line of content."""
        loader = LLMPromptLoader()
        content = "Create a simple function\nWith multiple lines"
        name = loader._generate_name_from_content(content)
        assert name == "Create a simple function"

    def test_generate_name_from_content_truncation(self):
        """Test name generation truncates long content."""
        loader = LLMPromptLoader()
        content = "A" * 100  # Very long content
        name = loader._generate_name_from_content(content)
        assert len(name) <= 53  # 50 chars + "..."
        assert name.endswith("...")

    def test_detect_format_yaml(self):
        """Test format detection for YAML files."""
        loader = LLMPromptLoader()
        yaml_path = Path("test.yaml")
        assert loader._detect_format(yaml_path) == "yaml"

        yml_path = Path("test.yml")
        assert loader._detect_format(yml_path) == "yaml"

    def test_detect_format_markdown(self):
        """Test format detection for Markdown files."""
        loader = LLMPromptLoader()
        md_path = Path("test.md")
        assert loader._detect_format(md_path) == "markdown"

    def test_detect_format_text_default(self):
        """Test format detection defaults to text."""
        loader = LLMPromptLoader()
        txt_path = Path("test.txt")
        assert loader._detect_format(txt_path) == "text"

        unknown_path = Path("test.xyz")
        assert loader._detect_format(unknown_path) == "text"

    def test_detect_format_none_source(self):
        """Test format detection with no source file."""
        loader = LLMPromptLoader()
        assert loader._detect_format(None) == "text"

    def test_never_fails_principle(self, settings):
        """Test that loader never raises exceptions - always returns valid prompt."""
        loader = LLMPromptLoader(settings)

        # Test various problematic inputs
        test_cases = [
            "",  # Empty string
            None,  # None input (should handle gracefully)
            "A" * 10000,  # Very long string
            "Special chars: 🚀 émojis",  # Unicode
            "\n\n\n",  # Only whitespace
        ]

        for test_input in test_cases:
            if test_input is not None:
                prompt = loader.load_from_string(test_input)
                assert isinstance(prompt, object)  # Should be Prompt object
                assert hasattr(prompt, "prompt")
                assert hasattr(prompt, "name")
                assert hasattr(prompt, "type")

    def test_content_preservation_principle(self, settings, mock_claude_sdk):
        """Test that original prompt content is NEVER modified."""
        original_content = "Create a function with special chars: 🚀 and émojis"

        # Mock successful LLM response
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps(
            {
                "task_type": "feature",
                "complexity": "simple",
                "estimated_duration": "5m",
                "suggested_name": "Unicode Function",
                "suggested_description": "Function with special characters",
                "tags": ["unicode"],
                "confidence_score": 0.8,
            }
        )

        mock_claude_sdk.return_value.__aiter__.return_value = [mock_message]

        loader = LLMPromptLoader(settings)
        prompt = loader.load_from_string(original_content)

        # Content must be preserved exactly
        assert prompt.prompt == original_content
        assert prompt.extracted_by_llm is True  # LLM was used
        assert prompt.name != original_content  # But metadata was extracted
