"""Tests for result formatter."""

from prp_bench.reporting.formatter import ResultFormatter


class TestResultFormatter:
    """Test suite for ResultFormatter."""

    def test_init_default(self):
        """Test formatter initialization with defaults."""
        formatter = ResultFormatter()
        assert formatter.verbose is False

    def test_init_verbose(self):
        """Test formatter initialization with verbose mode."""
        formatter = ResultFormatter(verbose=True)
        assert formatter.verbose is True

    def test_display_session_created(self, capsys):
        """Test session creation display."""
        formatter = ResultFormatter()
        formatter.display_session_created("test-123")

        captured = capsys.readouterr()
        assert "📋 Created session: test-123" in captured.out

    def test_display_tool_starting(self, capsys):
        """Test tool starting display."""
        formatter = ResultFormatter()
        formatter.display_tool_starting("claude", 300)

        captured = capsys.readouterr()
        assert "🤖 Running CLAUDE via SDK... (timeout: 300s)" in captured.out

    def test_display_tool_success(self, capsys):
        """Test tool success display."""
        formatter = ResultFormatter()
        formatter.display_tool_success("claude", 12.5)

        captured = capsys.readouterr()
        assert "✅ CLAUDE completed in 12.5 seconds" in captured.out

    def test_display_tool_failure(self, capsys):
        """Test tool failure display."""
        formatter = ResultFormatter()
        formatter.display_tool_failure("claude", "Timeout error")

        captured = capsys.readouterr()
        assert "❌ CLAUDE failed: Timeout error" in captured.out

    def test_display_llm_extraction(self, capsys):
        """Test LLM extraction display."""
        formatter = ResultFormatter()
        formatter.display_llm_extraction(0.85)

        captured = capsys.readouterr()
        assert "🧠 LLM extracted metadata (confidence: 0.85)" in captured.out
