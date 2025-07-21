"""Integration tests for LLM-powered prompt processing system."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from prp_bench.prompts.llm_loader import LLMPromptLoader
from prp_bench.prompts.loader import load_prompts_from_directory


class TestIntegration:
    """End-to-end integration tests."""

    def test_backward_compatibility_yaml_files(self, temp_yaml_file):
        """Test that existing YAML files work identically to before."""
        # Load with new LLM loader
        loader = LLMPromptLoader()
        prompt = loader.load_from_file(temp_yaml_file)

        # Verify all expected fields are present and correct
        assert prompt.name == "Test: Simple Function"
        assert prompt.description == "Create a simple Python function"
        assert prompt.type.value == "feature"
        assert prompt.complexity.value == "simple"
        assert prompt.tags == ["test", "python"]
        assert "Create a Python function that adds two numbers" in prompt.prompt

        # Verify it uses existing metadata (not LLM)
        assert prompt.extracted_by_llm is False
        assert prompt.original_format == "yaml"

    def test_backward_compatibility_markdown_files(self, temp_markdown_file, mock_claude_sdk):
        """Test that existing Markdown files still work with LLM enhancement."""
        # Mock LLM response
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps(
            {
                "task_type": "feature",
                "complexity": "simple",
                "estimated_duration": "2m",
                "suggested_name": "Hello World Script",
                "suggested_description": "Create greeting script",
                "tags": ["python", "hello"],
                "confidence_score": 0.8,
            }
        )
        mock_claude_sdk.return_value.__aiter__.return_value = [mock_message]

        loader = LLMPromptLoader()
        prompt = loader.load_from_file(temp_markdown_file)

        # Content should be preserved
        assert "Create a simple Python script" in prompt.prompt
        assert "hello.py" in prompt.prompt

        # But now has intelligent metadata
        assert prompt.extracted_by_llm is True
        assert "Hello World" in prompt.name  # LLM may generate slightly different names
        assert prompt.original_format == "markdown"

    def test_directory_loading_never_fails(self, mock_claude_sdk):
        """Test that directory loading handles all file types gracefully."""
        # Create temporary directory with mixed files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create various file types
            (temp_path / "good.yaml").write_text("""
name: "Good YAML"
description: "Valid YAML file"
type: "feature"
complexity: "simple"
prompt: "Create a good function"
            """)

            (temp_path / "bad.yaml").write_text("""
name: broken
bad_yaml: {
invalid
            """)

            (temp_path / "simple.md").write_text("# Simple Task\nCreate a function")
            (temp_path / "empty.txt").write_text("")
            (temp_path / "unicode.md").write_text("Create émoji function 🚀")

            # Mock LLM responses for non-YAML files
            mock_message = MagicMock()
            mock_message.content = [MagicMock()]
            mock_message.content[0].text = json.dumps(
                {
                    "task_type": "feature",
                    "complexity": "simple",
                    "estimated_duration": "5m",
                    "suggested_name": "Generated Name",
                    "suggested_description": "Generated description",
                    "tags": ["test"],
                    "confidence_score": 0.7,
                }
            )
            mock_claude_sdk.return_value.__aiter__.return_value = [mock_message]

            # Load all prompts - should never fail
            prompts = load_prompts_from_directory(temp_path)

            # All files should be loaded as valid prompts
            assert len(prompts) == 5  # All 5 files become prompts

            # Verify different handling strategies
            names = [p.name for p in prompts]
            assert "Good YAML" in names  # From valid YAML
            assert any(
                "bad.yaml" in name or "broken" in name for name in names
            )  # Fallback for bad YAML

            # All should have valid content
            for prompt in prompts:
                assert prompt.prompt != ""  # No empty prompts
                assert prompt.type is not None
                assert prompt.complexity is not None

    def test_cli_prompt_flag_functionality(self, mock_claude_sdk, mocker):
        """Test that CLI --prompt flag works end-to-end."""
        # Mock subprocess calls for tool availability
        mock_subprocess = mocker.patch("subprocess.run")
        mock_subprocess.return_value.returncode = 0

        # Mock orchestrator execution
        mock_orchestrator_class = mocker.patch("prp_bench.main.Orchestrator")
        mock_orchestrator = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.timing.execution_duration_seconds = 5.2
        mock_result.file_changes = []
        mock_orchestrator.execute_tool_via_sdk.return_value = mock_result
        mock_orchestrator_class.return_value = mock_orchestrator

        # Mock LLM response for prompt processing
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps(
            {
                "task_type": "feature",
                "complexity": "simple",
                "estimated_duration": "3m",
                "suggested_name": "CLI Test Function",
                "suggested_description": "Function from CLI",
                "tags": ["cli", "test"],
                "confidence_score": 0.85,
            }
        )
        mock_claude_sdk.return_value.__aiter__.return_value = [mock_message]

        # Mock click.echo to capture output
        mock_echo = mocker.patch("click.echo")

        # Test CLI with --prompt flag
        from click.testing import CliRunner

        from prp_bench.main import run_sdk as cli_run

        runner = CliRunner()
        result = runner.invoke(
            cli_run, ["--prompt", "Create a simple test function", "--tool", "claude", "--cleanup"]
        )

        # Should succeed
        assert result.exit_code == 0

        # Should show LLM extraction info
        echo_calls = [call[0][0] for call in mock_echo.call_args_list]
        assert any("LLM extracted metadata" in call for call in echo_calls)
        assert any("Claude completed" in call for call in echo_calls)

    def test_error_resilience_malformed_inputs(self, mock_claude_sdk):
        """Test that system handles malformed inputs gracefully."""
        # Mock LLM to sometimes fail
        mock_claude_sdk.side_effect = Exception("Network error")

        loader = LLMPromptLoader()

        malformed_inputs = [
            "{'invalid': json}",  # Invalid JSON-like
            "\x00\x01\x02",  # Binary data
            "A" * 100000,  # Extremely long input
            "",  # Empty
            "\n\n\n",  # Only whitespace
            "🚀" * 1000,  # Unicode spam
        ]

        for malformed_input in malformed_inputs:
            prompt = loader.load_from_string(malformed_input)

            # Should always succeed
            assert prompt is not None
            assert prompt.prompt == malformed_input  # Content preserved
            assert prompt.fallback_applied is True
            assert prompt.type is not None
            assert prompt.complexity is not None

    def test_performance_simple_prompts(self, settings, mock_claude_sdk):
        """Test that simple prompts process quickly."""
        import time

        # Mock fast LLM response
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps(
            {
                "task_type": "feature",
                "complexity": "simple",
                "estimated_duration": "1m",
                "suggested_name": "Quick Task",
                "suggested_description": "Fast processing",
                "tags": ["quick"],
                "confidence_score": 0.9,
            }
        )
        mock_claude_sdk.return_value.__aiter__.return_value = [mock_message]

        loader = LLMPromptLoader(settings)

        start_time = time.time()
        prompt = loader.load_from_string("Create a simple function")
        end_time = time.time()

        # Should process quickly (mocked, so should be instant)
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Under 1 second with mocked SDK

        # Should have extracted metadata successfully
        assert prompt.extracted_by_llm is True
        assert prompt.name == "Quick Task"

    def test_content_preservation_end_to_end(
        self, temp_yaml_file, temp_markdown_file, mock_claude_sdk
    ):
        """Test that content is NEVER modified through the entire pipeline."""
        # Mock LLM response
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = json.dumps(
            {
                "task_type": "feature",
                "complexity": "medium",
                "estimated_duration": "10m",
                "suggested_name": "Complex Task",
                "suggested_description": "Complex processing",
                "tags": ["complex"],
                "confidence_score": 0.7,
            }
        )
        mock_claude_sdk.return_value.__aiter__.return_value = [mock_message]

        # Read original content
        original_md_content = temp_markdown_file.read_text()

        loader = LLMPromptLoader()

        # Process through loader
        yaml_prompt = loader.load_from_file(temp_yaml_file)
        md_prompt = loader.load_from_file(temp_markdown_file)

        # YAML prompt content should be from the 'prompt' field
        assert "Create a Python function that adds two numbers" in yaml_prompt.prompt

        # Markdown content should be preserved exactly
        assert md_prompt.prompt == original_md_content

        # Neither should have the file structure in the prompt content
        assert "name:" not in yaml_prompt.prompt
        assert "description:" not in yaml_prompt.prompt

    def test_mixed_confidence_handling(self, mock_claude_sdk, settings):
        """Test system handling of mixed confidence scenarios."""
        loader = LLMPromptLoader(settings)

        # Test sequence of different confidence levels
        confidence_scenarios = [
            (0.9, False),  # High confidence, should use LLM
            (0.4, True),  # Low confidence, should use smart fallback
            (0.7, False),  # Medium-high confidence, should use LLM
        ]

        for confidence, should_fallback in confidence_scenarios:
            mock_message = MagicMock()
            mock_message.content = [MagicMock()]
            mock_message.content[0].text = json.dumps(
                {
                    "task_type": "feature",
                    "complexity": "simple",
                    "estimated_duration": "5m",
                    "suggested_name": f"Task {confidence}",
                    "suggested_description": f"Confidence {confidence}",
                    "tags": ["test"],
                    "confidence_score": confidence,
                }
            )
            mock_claude_sdk.return_value.__aiter__.return_value = [mock_message]

            prompt = loader.load_from_string(f"Test prompt {confidence}")

            assert prompt.extracted_by_llm is True
            assert prompt.extraction_confidence == confidence
            assert prompt.fallback_applied == should_fallback

            if should_fallback:
                # Low confidence should use safe defaults
                assert prompt.type.value == "feature"
                assert prompt.complexity.value == "simple"
            else:
                # High confidence should use LLM suggestions
                assert prompt.name == f"Task {confidence}"
