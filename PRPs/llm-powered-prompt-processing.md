name: "LLM-Powered Prompt Processing Redesign"
description: |
Replace complex parsing logic with Claude Code SDK-powered metadata extraction that never fails and preserves original prompt content. Simplify architecture by removing 500+ lines of rigid parsing code and implement intelligent LLM-powered metadata extraction with graceful fallbacks.

## Purpose

Transform PRP-Bench from a rigid YAML parser to an intelligent LLM-powered prompt processor that can handle any text input while extracting useful metadata. This aligns with CLAUDE.md principles of KISS (Keep It Simple, Stupid) and YAGNI (You Aren't Gonna Need It) by removing speculative complexity.

## Core Principles

1. **Never Fail**: Any text input becomes a valid prompt
2. **Preserve Content**: Original prompt content never modified
3. **LLM Intelligence**: Smart metadata extraction vs rigid parsing
4. **Graceful Degradation**: Intelligent fallbacks for all failure modes
5. **Backward Compatibility**: Support existing YAML, Markdown, and text formats

---

## Goal

Create an LLM-powered prompt processing system that:

- Accepts prompts via `--prompt "text"` CLI flag or any file format
- Uses Claude Code SDK to intelligently extract metadata without affecting prompt content
- Never fails - always produces a valid Prompt object with intelligent defaults
- Removes complex parsing logic (~500+ lines) in favor of simple LLM extraction
- Maintains all existing functionality while adding flexibility

## Why

- **User Experience**: Remove parsing failures that cause silent prompt skipping
- **Flexibility**: Support any text input format without rigid schema requirements
- **Intelligence**: LLM can understand context and complexity better than rules
- **Maintainability**: Simpler codebase with fewer edge cases to handle
- **Scalability**: Easy to add new metadata fields without breaking existing prompts

## What

Replace the current strict parsing system with:

### Current Problems

- YAML parsing fails silently on typos (e.g., `complexity: "easy"` vs `"simple"`)
- 5 required fields cause failures if any are missing
- Complex 279-line parser.py with rigid enum validation
- Directory loading silently skips failed prompts with warnings
- Runners bypass the strict parser anyway, making it unused complexity

### New Solution

- **Smart CLI**: Accept `--prompt "text"` or any file format
- **LLM Extraction**: Use Claude Code SDK to extract metadata from any text
- **Never Fail**: Always produce valid Prompt objects with intelligent defaults
- **Preserve Content**: Original prompt text sent unchanged to CLI tools
- **Graceful Fallbacks**: Intelligent defaults when extraction fails

### Success Criteria

- [ ] CLI accepts `--prompt "any text here"` flag
- [ ] Any file format (.md, .txt, .yaml, .json) loads successfully
- [ ] No prompt ever fails to parse - all become valid Prompt objects
- [ ] Original prompt content preserved exactly for CLI tool execution
- [ ] LLM extracts intelligent metadata (type, complexity, duration, tags)
- [ ] Graceful fallbacks work when LLM extraction fails
- [ ] Remove 500+ lines of complex parsing code
- [ ] All existing functionality maintained
- [ ] Performance: sub-second metadata extraction for simple prompts

## All Needed Context

### Documentation & References

```yaml
# MUST READ - Include these in your context window

# Claude Code SDK Integration
- url: https://docs.anthropic.com/en/docs/claude-code/sdk
  why: Primary SDK documentation for programmatic usage

- url: https://docs.anthropic.com/en/docs/claude-code/overview
  why: Understanding SDK vs CLI coordination patterns

# Pydantic v2 Patterns (Current codebase uses strict v2)
- url: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
  why: Settings management patterns to extend existing config.py

- url: https://docs.pydantic.dev/latest/concepts/validators/
  why: Custom validation patterns for LLM-extracted data

# Click CLI Framework (For new --prompt flag)
- url: https://click.palletsprojects.com/en/stable/advanced/
  why: Advanced CLI patterns for flag handling

# Key Implementation Files
- file: src/prp_bench/config.py
  why: Existing Pydantic settings pattern to extend for LLM config
  critical: Lines 121-142 show telemetry env setup pattern to follow

- file: src/prp_bench/models.py
  why: Complete data model architecture - extend, don't replace
  critical: Lines 78-93 show Prompt model structure to enhance

- file: src/prp_bench/orchestration/claude_orchestrator.py
  why: SDK integration patterns already implemented
  critical: Lines 240-256 show telemetry setup for SDK calls

- file: src/prp_bench/simple_runner.py
  why: Current prompt parsing pattern that works
  critical: Lines 42-47 show simple YAML vs text detection

- file: src/prp_bench/multi_cli.py
  why: Click CLI structure to extend with --prompt flag
  critical: Lines 12-29 show existing CLI option patterns

- file: src/prp_bench/prompts/loader.py
  why: Directory loading with error recovery pattern
  critical: Lines 56-66 show current error handling to replace

# Sample Prompt Formats (For LLM training examples)
- file: prompts/test/simple-function.prp.yaml
  why: Example of YAML metadata structure LLM should extract

- file: prompts/test/hello.md
  why: Simple markdown format the LLM should handle
```

### Current Codebase Tree

```bash
src/prp_bench/
├── __init__.py
├── config.py              # Extend with LLM settings
├── models.py               # Extend Prompt model
├── main.py                 # Add --prompt flag support
├── multi_cli.py            # Update CLI with new flag
├── orchestration/
│   ├── claude_orchestrator.py  # SDK patterns to reuse
│   └── session_manager.py      # Session management
├── prompts/
│   ├── loader.py           # REPLACE with LLM loader
│   ├── parser.py           # DELETE (279 lines)
│   └── validator.py        # DELETE (251 lines)
├── runner.py               # Update to use new loader
├── simple_runner.py        # Update prompt loading
└── gemini_runner.py        # Update prompt loading
```

### Desired Codebase Tree

```bash
src/prp_bench/
├── config.py              # + LLM configuration
├── models.py               # + LLM extraction fields
├── main.py                 # + --prompt CLI flag
├── multi_cli.py            # + --prompt CLI flag
├── orchestration/          # No changes needed
├── prompts/
│   ├── llm_loader.py       # NEW: LLM-powered loader
│   └── tests/              # NEW: Comprehensive tests
├── runner.py               # Use new llm_loader
├── simple_runner.py        # Use new llm_loader
└── tests/                  # NEW: Test infrastructure
    ├── conftest.py
    ├── test_llm_loader.py
    └── test_integration.py
```

### Known Gotchas of Our Codebase & Library Quirks

```python
# CRITICAL: Pydantic v2 strict mode (lines 78-93 in models.py)
# All models require explicit field definitions with Field()
# Migration pattern: Optional fields need default values or Optional[Type]

# CRITICAL: Claude Code SDK requires specific environment setup
# Lines 121-142 in config.py show correct OpenTelemetry pattern
env_vars = {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_RESOURCE_ATTRIBUTES": f"service.name=prp-bench"
}

# CRITICAL: Worktree isolation pattern (orchestration/claude_orchestrator.py)
# SDK calls must respect cwd=worktree_dir for proper isolation
# Never change working directory globally

# CRITICAL: Existing runners use simple parsing (lines 42-47)
# They bypass the complex parser.py - this is WHY it can be deleted
if prompt_file.suffix in [".yaml", ".yml"]:
    prompt_data = yaml.safe_load(f)
    prompt_content = prompt_data.get("prompt", "")
else:
    prompt_content = prompt_file.read_text()

# CRITICAL: Click CLI patterns (multi_cli.py lines 12-29)
# Use @click.option with proper type validation
# Maintain existing option names for backward compatibility

# CRITICAL: UV dependency management (CLAUDE.md lines 96-98)
# NEVER update pyproject.toml directly - use `uv add` only
# Add claude-code-sdk with: uv add claude-code-sdk

# GOTCHA: Testing infrastructure doesn't exist yet
# No tests/ directory or patterns exist - need to create from scratch
# Follow CLAUDE.md vertical slicing: tests next to code
```

## Implementation Blueprint

### Data Models and Structure

Extend existing Pydantic models with LLM-specific fields while maintaining backward compatibility:

```python
# models.py extensions - ADD these fields to existing Prompt class
class Prompt(BaseModel):  # Existing class - extend it
    # ... existing fields stay the same ...

    # NEW LLM-specific fields
    extracted_by_llm: bool = Field(default=False, description="Metadata extracted by LLM")
    extraction_confidence: float = Field(default=1.0, description="LLM confidence score")
    extraction_model: str | None = Field(default=None, description="Model used for extraction")
    fallback_applied: bool = Field(default=False, description="Whether fallback defaults used")
    original_format: str = Field(default="text", description="Original input format")

    # Make existing required fields optional with smart defaults
    name: str = Field(default="", description="Prompt name - will be generated if empty")
    description: str = Field(default="", description="Prompt description")
    type: PromptType = Field(default=PromptType.FEATURE, description="Prompt type")
    complexity: ComplexityLevel = Field(default=ComplexityLevel.SIMPLE, description="Complexity level")

# NEW: LLM extraction result model
class LLMExtractionResult(BaseModel):
    task_type: str = Field(..., description="Detected task type")
    complexity: str = Field(..., description="Estimated complexity")
    estimated_duration: str = Field(default="5m", description="Estimated duration")
    suggested_name: str = Field(default="", description="Suggested prompt name")
    suggested_description: str = Field(default="", description="One-line description")
    tags: list[str] = Field(default_factory=list, description="Relevant tags")
    confidence_score: float = Field(default=0.8, description="Extraction confidence")
    needs_human_review: bool = Field(default=False, description="Low confidence flag")
```

### List of Tasks to be Completed

```yaml
Task 1 - Extend Configuration:
MODIFY src/prp_bench/config.py:
  - ADD LLMConfig class with Claude Code SDK settings
  - ADD llm_enabled: bool = True to Settings class
  - ADD extraction_model: str = "claude-3-5-haiku-20241022" for fast extraction
  - ADD fallback_enabled: bool = True for graceful degradation
  - PRESERVE existing telemetry configuration (lines 121-142)

Task 2 - Extend Data Models:
MODIFY src/prp_bench/models.py:
  - ADD LLM-specific fields to existing Prompt class (don't break it)
  - ADD LLMExtractionResult model for structured extraction
  - MAKE existing required fields optional with defaults
  - ADD validation for LLM confidence thresholds

Task 3 - Create LLM-Powered Loader:
CREATE src/prp_bench/prompts/llm_loader.py:
  - IMPLEMENT LLMPromptLoader class with Claude Code SDK integration
  - METHOD load_from_file(file_path: Path) -> Prompt
  - METHOD load_from_string(prompt_text: str) -> Prompt
  - METHOD _extract_metadata_with_claude(content: str) -> LLMExtractionResult
  - METHOD _apply_intelligent_defaults(content: str) -> dict
  - FOLLOW existing error handling patterns from orchestrator.py

Task 4 - Add CLI --prompt Flag:
MODIFY src/prp_bench/multi_cli.py:
  - ADD @click.option("--prompt", "-p", help="Direct prompt text")
  - UPDATE run() function to handle both file and text input
  - MAINTAIN backward compatibility with existing file arguments
  - FOLLOW existing Click patterns (lines 12-29)

Task 5 - Update Runners:
MODIFY src/prp_bench/simple_runner.py AND src/prp_bench/gemini_runner.py:
  - REPLACE manual YAML parsing with LLMPromptLoader calls
  - MAINTAIN existing prompt_content extraction (lines 42-47 pattern)
  - PRESERVE original prompt content for CLI tool execution
  - ADD error handling for LLM failures with fallbacks

Task 6 - Update Main CLI:
MODIFY src/prp_bench/main.py:
  - UPDATE load_prompt_file() to use LLMPromptLoader
  - ADD support for --prompt flag in main CLI
  - MAINTAIN existing file path handling

Task 7 - Delete Complex Parsers:
DELETE src/prp_bench/prompts/parser.py (279 lines of rigid parsing)
DELETE src/prp_bench/prompts/validator.py (251 lines - validation moves to runtime)
UPDATE src/prp_bench/prompts/loader.py to use LLMPromptLoader

Task 8 - Add Dependencies:
ADD to pyproject.toml using UV:
  - uv add claude-code-sdk
  - uv add pytest-asyncio (for async testing)
  - PRESERVE existing dependencies unchanged

Task 9 - Create Test Infrastructure:
CREATE src/prp_bench/tests/ directory structure:
  - CREATE conftest.py with pytest fixtures
  - CREATE test_llm_loader.py with comprehensive unit tests
  - CREATE test_integration.py with end-to-end tests
  - FOLLOW CLAUDE.md vertical slicing pattern

Task 10 - Integration Testing:
CREATE comprehensive test coverage:
  - Test LLM extraction with various input formats
  - Test graceful fallbacks when LLM fails
  - Test CLI --prompt flag functionality
  - Test backward compatibility with existing files
  - Mock Claude Code SDK for fast unit tests
```

### Task 1 Pseudocode - Configuration Extension

```python
# config.py - ADD to existing Settings class
class LLMConfig(BaseModel):
    """LLM-specific configuration for prompt processing."""
    enabled: bool = Field(default=True, description="Enable LLM extraction")
    model: str = Field(default="claude-3-5-haiku-20241022", description="Fast model for extraction")
    timeout_seconds: int = Field(default=30, description="LLM call timeout")
    max_retries: int = Field(default=3, description="Retry attempts")
    confidence_threshold: float = Field(default=0.6, description="Min confidence for acceptance")
    fallback_enabled: bool = Field(default=True, description="Use fallbacks when LLM fails")

class Settings(BaseSettings):  # Existing class - extend it
    # ... existing fields unchanged ...

    # ADD new LLM configuration
    llm: LLMConfig = Field(default_factory=LLMConfig)

    def get_llm_env_vars(self) -> dict[str, str]:
        """Get environment variables for Claude Code SDK."""
        env_vars = self.get_telemetry_env_vars()  # Reuse existing telemetry setup
        if self.llm.enabled:
            env_vars.update({
                "CLAUDE_CODE_SDK_TIMEOUT": str(self.llm.timeout_seconds),
                "CLAUDE_CODE_SDK_MODEL": self.llm.model
            })
        return env_vars
```

### Task 3 Pseudocode - LLM-Powered Loader Core Logic

```python
# prompts/llm_loader.py - NEW file
from claude_code_sdk import query, ClaudeCodeOptions
import asyncio
import json
from pathlib import Path

class LLMPromptLoader:
    """LLM-powered prompt loader that never fails."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm_config = settings.llm

    def load_from_file(self, file_path: Path) -> Prompt:
        """Load prompt from any file format."""
        try:
            # Extract content (handle YAML, Markdown, text)
            content = self._extract_content_from_file(file_path)
            return self.load_from_string(content, source_file=file_path)
        except Exception as e:
            # NEVER FAIL - create basic prompt with file content
            return self._create_fallback_prompt(file_path.read_text(), source_file=file_path, error=str(e))

    def load_from_string(self, prompt_text: str, source_file: Path = None) -> Prompt:
        """Load prompt from text with LLM extraction."""
        if not self.llm_config.enabled:
            return self._create_fallback_prompt(prompt_text, source_file)

        try:
            # Try LLM extraction
            extraction = asyncio.run(self._extract_metadata_with_claude(prompt_text))

            if extraction.confidence_score >= self.llm_config.confidence_threshold:
                # High confidence - use LLM metadata
                return Prompt(
                    name=extraction.suggested_name or self._generate_name_from_content(prompt_text),
                    description=extraction.suggested_description or f"Extracted from text",
                    type=PromptType(extraction.task_type),
                    complexity=ComplexityLevel(extraction.complexity),
                    tags=extraction.tags,
                    prompt=prompt_text,  # NEVER MODIFY original content
                    extracted_by_llm=True,
                    extraction_confidence=extraction.confidence_score,
                    extraction_model=self.llm_config.model,
                    source_file=source_file
                )
            else:
                # Low confidence - use intelligent fallbacks
                return self._create_smart_fallback(prompt_text, extraction, source_file)

        except Exception as e:
            # LLM failed - use intelligent defaults
            return self._create_fallback_prompt(prompt_text, source_file, error=str(e))

    async def _extract_metadata_with_claude(self, content: str) -> LLMExtractionResult:
        """Use Claude Code SDK for metadata extraction."""
        extraction_prompt = f"""
        Analyze this coding prompt and extract metadata as JSON:

        {content}

        Extract:
        - task_type: "feature" | "bug" | "refactor" | "test" | "docs"
        - complexity: "simple" | "medium" | "complex"
        - estimated_duration: "2m", "1h", "1d" format
        - suggested_name: Brief descriptive name
        - suggested_description: One sentence description
        - tags: Array of relevant tags
        - confidence_score: 0.0-1.0 confidence in extraction

        Return only valid JSON, no explanations.
        """

        options = ClaudeCodeOptions(
            model=self.llm_config.model,  # Use fast Haiku model
            max_turns=1,
            json_output=True,
            cwd=str(Path.cwd())  # Maintain isolation
        )

        results = []
        async for message in query(extraction_prompt, options=options):
            results.append(message)

        response_text = "".join(results)
        extracted_data = json.loads(response_text)
        return LLMExtractionResult(**extracted_data)
```

### Integration Points

```yaml
CLI_ENHANCEMENT:
  - add_to: src/prp_bench/multi_cli.py
  - pattern: "@click.option('--prompt', '-p', help='Direct prompt text')"
  - integration: "if prompt: use LLMPromptLoader.load_from_string(prompt)"

CONFIGURATION:
  - extend: src/prp_bench/config.py
  - pattern: "settings.llm.enabled and settings.llm.model"
  - integration: "get_llm_env_vars() method for SDK setup"

MODEL_EXTENSION:
  - extend: src/prp_bench/models.py
  - pattern: "extracted_by_llm: bool = Field(default=False)"
  - integration: "Backward compatible - all existing code works"

SDK_INTEGRATION:
  - reuse: src/prp_bench/orchestration/claude_orchestrator.py patterns
  - pattern: "env = self._setup_telemetry_env()"
  - integration: "Same env setup for SDK calls in loader"
```

## Validation Loop

### Level 1: Syntax & Style

```bash
# Run these FIRST - fix any errors before proceeding
uv add claude-code-sdk                    # Add required dependency
ruff check src/prp_bench/ --fix          # Auto-fix style issues
mypy src/prp_bench/                       # Type checking (strict mode)

# Expected: No errors. If errors, READ and fix based on existing patterns.
# Pay attention to Pydantic v2 strict mode requirements in models.py
```

### Level 2: Unit Tests - Create Comprehensive Test Suite

```python
# CREATE src/prp_bench/tests/conftest.py
@pytest.fixture
def settings():
    """Test settings with LLM enabled."""
    return Settings(llm=LLMConfig(enabled=True, model="claude-3-5-haiku-20241022"))

@pytest.fixture
def mock_claude_sdk(mocker):
    """Mock Claude Code SDK for testing."""
    mock_query = mocker.patch('claude_code_sdk.query')
    mock_query.return_value = AsyncMock()
    return mock_query

# CREATE src/prp_bench/tests/test_llm_loader.py
def test_load_from_string_success(settings, mock_claude_sdk):
    """Test successful LLM extraction."""
    # Mock LLM response
    mock_claude_sdk.return_value.__aiter__.return_value = [
        '{"task_type": "feature", "complexity": "simple", "confidence_score": 0.9}'
    ]

    loader = LLMPromptLoader(settings)
    prompt = loader.load_from_string("Create a hello world function")

    assert prompt.extracted_by_llm is True
    assert prompt.extraction_confidence == 0.9
    assert prompt.type == PromptType.FEATURE
    assert prompt.prompt == "Create a hello world function"  # Unchanged

def test_fallback_when_llm_fails(settings, mock_claude_sdk):
    """Test graceful fallback when LLM extraction fails."""
    mock_claude_sdk.side_effect = Exception("API Error")

    loader = LLMPromptLoader(settings)
    prompt = loader.load_from_string("Any text here")

    assert prompt.fallback_applied is True
    assert prompt.prompt == "Any text here"  # Content preserved
    assert prompt.type == PromptType.FEATURE  # Default type

def test_yaml_file_compatibility(settings, mock_claude_sdk):
    """Test existing YAML files still work."""
    # Test with existing prompts/test/simple-function.prp.yaml
    loader = LLMPromptLoader(settings)
    prompt = loader.load_from_file(Path("prompts/test/simple-function.prp.yaml"))

    assert prompt.name == "Test: Simple Function"  # From YAML metadata
    assert prompt.prompt.startswith("Create a Python function")  # Content preserved
```

```bash
# Run and iterate until passing - CREATE tests that match existing patterns
uv run pytest src/prp_bench/tests/test_llm_loader.py -v
# If failing: Read error, fix code, re-run. Never skip failing tests.
```

### Level 3: Integration Testing

```bash
# Test CLI with new --prompt flag
uv run prp-bench-multi --prompt "Create a simple REST API endpoint" --tool claude -v

# Expected:
# - Prompt processed successfully with LLM extraction
# - Original content passed unchanged to Claude
# - Metadata extracted and displayed
# - Tool execution works normally

# Test backward compatibility
uv run prp-bench-multi prompts/test/simple-function.prp.yaml --tool claude

# Expected: Existing YAML files work identically to before
```

### Level 4: End-to-End Validation

```bash
# Test various input formats
echo "Fix the bug in the login system" | uv run prp-bench-multi --prompt -
uv run prp-bench-multi prompts/test/hello.md --tool gemini
uv run prp-bench-multi --prompt "Refactor the database layer for better performance" --tool both

# Test error handling
uv run prp-bench-multi --prompt "malformed input with émojis and weird chars 🚀" --tool claude

# Expected: All inputs work, no parsing failures, original content preserved
```

### Level 5: Performance & Monitoring

```bash
# Test LLM extraction speed
time uv run python -c "
from src.prp_bench.prompts.llm_loader import LLMPromptLoader
from src.prp_bench.config import Settings
loader = LLMPromptLoader(Settings())
prompt = loader.load_from_string('Create a function that adds two numbers')
print(f'Extracted: {prompt.type}, Confidence: {prompt.extraction_confidence}')
"

# Expected: Sub-second response for simple prompts
# Expected: Telemetry data shows token usage and costs

# Monitor telemetry
uv run prp-bench-multi --prompt "Complex system architecture design" --tool claude -v
# Expected: OpenTelemetry metrics show LLM extraction calls separate from execution
```

## Final Validation Checklist

- [ ] Dependency added: `uv add claude-code-sdk` succeeds
- [ ] All tests pass: `uv run pytest src/prp_bench/tests/ -v`
- [ ] No linting errors: `uv run ruff check src/prp_bench/`
- [ ] No type errors: `uv run mypy src/prp_bench/`
- [ ] CLI --prompt flag works: `uv run prp-bench-multi --prompt "test"`
- [ ] Backward compatibility: Existing YAML/MD files work identically
- [ ] Error resilience: Malformed inputs don't crash, produce valid prompts
- [ ] Performance: Simple prompts extract metadata in <5 seconds
- [ ] Content preservation: Original prompt text never modified
- [ ] Telemetry working: OpenTelemetry shows extraction metrics
- [ ] Complex parsing removed: parser.py and validator.py deleted
- [ ] Integration passes: All existing tools work with new loader

---

## Anti-Patterns to Avoid

- ❌ Don't modify prompt content during extraction - preserve it exactly
- ❌ Don't fail when LLM extraction fails - always provide graceful fallback
- ❌ Don't break existing YAML/Markdown file compatibility
- ❌ Don't skip creating comprehensive tests - this is critical for reliability
- ❌ Don't ignore confidence scores - use them for intelligent fallbacks
- ❌ Don't hardcode LLM prompts - make them configurable and iterative
- ❌ Don't bypass existing telemetry patterns - integrate with OpenTelemetry setup
- ❌ Don't create new CLI patterns - follow existing Click conventions
- ❌ Don't ignore timeout handling - LLM calls can be slow or hang
- ❌ Don't assume Claude Code SDK is always available - handle CLI fallbacks

---
