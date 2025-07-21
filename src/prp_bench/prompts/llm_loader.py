"""LLM-powered prompt loader that never fails and preserves original content."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import yaml
from claude_code_sdk import ClaudeCodeOptions, query

from ..config import Settings, get_settings
from ..models import (
    ComplexityLevel,
    LLMExtractionResult,
    Prompt,
    PromptMetadata,
    PromptType,
)

logger = logging.getLogger(__name__)


class LLMPromptLoader:
    """LLM-powered prompt loader that never fails."""

    def __init__(self, settings: Settings | None = None):
        """Initialize LLM prompt loader.

        Args:
            settings: Optional settings instance
        """
        self.settings = settings or get_settings()
        self.llm_config = self.settings.llm

    def load_from_file(self, file_path: Path) -> Prompt:
        """Load prompt from any file format.

        Args:
            file_path: Path to prompt file

        Returns:
            Valid Prompt object (never fails)
        """
        try:
            # Extract content and existing metadata (handle YAML, Markdown, text)
            content, existing_metadata = self._extract_content_from_file(file_path)
            return self.load_from_string(
                content, source_file=file_path, existing_metadata=existing_metadata
            )
        except Exception as e:
            logger.warning(f"Error loading file {file_path}: {e}")
            # NEVER FAIL - create basic prompt with file content
            try:
                raw_content = file_path.read_text(encoding="utf-8")
            except Exception:
                raw_content = f"Error reading file: {file_path}"

            return self._create_fallback_prompt(raw_content, source_file=file_path, error=str(e))

    def load_from_string(
        self,
        prompt_text: str,
        source_file: Path | None = None,
        existing_metadata: dict[str, Any] | None = None,
    ) -> Prompt:
        """Load prompt from text with LLM extraction.

        Args:
            prompt_text: Prompt text content
            source_file: Optional source file path
            existing_metadata: Optional existing metadata from file

        Returns:
            Valid Prompt object (never fails)
        """
        # If we have existing metadata (from YAML), use it and skip LLM
        if existing_metadata:
            return self._create_prompt_from_metadata(prompt_text, existing_metadata, source_file)

        # Try LLM extraction if enabled
        if not self.llm_config.enabled:
            return self._create_fallback_prompt(prompt_text, source_file)

        try:
            # Try LLM extraction
            extraction = asyncio.run(self._extract_metadata_with_claude(prompt_text))

            if extraction.confidence_score >= self.llm_config.confidence_threshold:
                # High confidence - use LLM metadata
                return self._create_prompt_from_extraction(prompt_text, extraction, source_file)
            else:
                # Low confidence - use intelligent fallbacks
                return self._create_smart_fallback(prompt_text, extraction, source_file)

        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}")
            # LLM failed - use intelligent defaults
            return self._create_fallback_prompt(prompt_text, source_file, error=str(e))

    def _extract_content_from_file(self, file_path: Path) -> tuple[str, dict[str, Any] | None]:
        """Extract content and metadata from file.

        Args:
            file_path: Path to file

        Returns:
            Tuple of (content, existing_metadata)
        """
        file_content = file_path.read_text(encoding="utf-8")

        if file_path.suffix in [".yaml", ".yml"]:
            # YAML file - extract existing metadata
            try:
                yaml_data = yaml.safe_load(file_content)
                if isinstance(yaml_data, dict) and "prompt" in yaml_data:
                    prompt_content = yaml_data.pop("prompt", "")
                    return prompt_content, yaml_data
                else:
                    # Treat whole file as prompt content
                    return file_content, None
            except yaml.YAMLError:
                # Invalid YAML - treat as text
                return file_content, None
        else:
            # Markdown or text file - no existing metadata
            return file_content, None

    async def _extract_metadata_with_claude(self, content: str) -> LLMExtractionResult:
        """Use Claude Code SDK for metadata extraction.

        Args:
            content: Prompt content to analyze

        Returns:
            Extraction results with confidence score
        """
        extraction_prompt = f"""
Analyze this coding prompt and extract metadata as JSON:

{content}

Extract:
- task_type: "feature" | "bug" | "refactor" | "test" | "docs"
- complexity: "simple" | "medium" | "complex"
- estimated_duration: "2m", "1h", "1d" format
- suggested_name: Brief descriptive name (max 50 chars)
- suggested_description: One sentence description (max 100 chars)
- tags: Array of relevant tags (max 5)
- confidence_score: 0.0-1.0 confidence in extraction

Return only valid JSON, no explanations.
        """

        # Use Claude Code SDK with fast Haiku model
        options = ClaudeCodeOptions(
            cwd=str(Path.cwd()),  # Maintain isolation
            max_turns=1,
        )

        try:
            response_messages = []
            async for message in query(prompt=extraction_prompt, options=options):
                response_messages.append(message)

            # Extract text content from messages
            response_text = ""
            for message in response_messages:
                if hasattr(message, "content") and message.content:
                    for block in message.content:
                        if hasattr(block, "text"):
                            response_text += block.text

            # Clean up JSON response
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            extracted_data = json.loads(response_text.strip())
            return LLMExtractionResult(**extracted_data)

        except Exception as e:
            logger.warning(f"Claude extraction failed: {e}")
            # Return low-confidence fallback
            return LLMExtractionResult(
                task_type="feature",
                complexity="simple",
                confidence_score=0.0,
                needs_human_review=True,
            )

    def _create_prompt_from_metadata(
        self, prompt_text: str, metadata: dict[str, Any], source_file: Path | None = None
    ) -> Prompt:
        """Create prompt from existing metadata (YAML format).

        Args:
            prompt_text: Prompt content
            metadata: Existing metadata from file
            source_file: Source file path

        Returns:
            Prompt object with existing metadata
        """
        try:
            return Prompt(
                name=metadata.get("name", ""),
                description=metadata.get("description", ""),
                type=PromptType(metadata.get("type", "feature")),
                complexity=ComplexityLevel(metadata.get("complexity", "simple")),
                tags=metadata.get("tags", []),
                meta=PromptMetadata(**metadata.get("meta", {})),
                prompt=prompt_text,
                source_file=source_file,
                extracted_by_llm=False,
                original_format="yaml"
                if source_file and source_file.suffix in [".yaml", ".yml"]
                else "text",
            )
        except Exception as e:
            logger.warning(f"Error parsing metadata: {e}")
            # Fallback to simple prompt
            return self._create_fallback_prompt(prompt_text, source_file)

    def _create_prompt_from_extraction(
        self, prompt_text: str, extraction: LLMExtractionResult, source_file: Path | None = None
    ) -> Prompt:
        """Create prompt from LLM extraction results.

        Args:
            prompt_text: Original prompt content
            extraction: LLM extraction results
            source_file: Source file path

        Returns:
            Prompt object with LLM-extracted metadata
        """
        try:
            return Prompt(
                name=extraction.suggested_name or self._generate_name_from_content(prompt_text),
                description=extraction.suggested_description or "Extracted from text",
                type=PromptType(extraction.task_type),
                complexity=ComplexityLevel(extraction.complexity),
                tags=extraction.tags,
                meta=PromptMetadata(expected_duration=extraction.estimated_duration),
                prompt=prompt_text,  # NEVER MODIFY original content
                source_file=source_file,
                extracted_by_llm=True,
                extraction_confidence=extraction.confidence_score,
                extraction_model=self.llm_config.model,
                original_format=self._detect_format(source_file),
            )
        except Exception as e:
            logger.warning(f"Error creating prompt from extraction: {e}")
            return self._create_fallback_prompt(prompt_text, source_file)

    def _create_smart_fallback(
        self, prompt_text: str, extraction: LLMExtractionResult, source_file: Path | None = None
    ) -> Prompt:
        """Create prompt with smart fallbacks for low-confidence extraction.

        Args:
            prompt_text: Original prompt content
            extraction: LLM extraction (low confidence)
            source_file: Source file path

        Returns:
            Prompt object with smart defaults
        """
        return Prompt(
            name=extraction.suggested_name or self._generate_name_from_content(prompt_text),
            description=extraction.suggested_description or "Smart fallback description",
            type=PromptType.FEATURE,  # Safe default
            complexity=ComplexityLevel.SIMPLE,  # Safe default
            tags=extraction.tags[:3] if extraction.tags else [],  # Limit tags
            meta=PromptMetadata(expected_duration="5m"),
            prompt=prompt_text,
            source_file=source_file,
            extracted_by_llm=True,
            extraction_confidence=extraction.confidence_score,
            extraction_model=self.llm_config.model,
            fallback_applied=True,
            original_format=self._detect_format(source_file),
        )

    def _create_fallback_prompt(
        self, prompt_text: str, source_file: Path | None = None, error: str | None = None
    ) -> Prompt:
        """Create basic fallback prompt when all else fails.

        Args:
            prompt_text: Original prompt content
            source_file: Source file path
            error: Optional error message

        Returns:
            Basic prompt object with defaults
        """
        if error:
            logger.warning(f"Using fallback prompt due to error: {error}")

        return Prompt(
            name=self._generate_name_from_content(prompt_text),
            description="Fallback prompt with default settings",
            type=PromptType.FEATURE,
            complexity=ComplexityLevel.SIMPLE,
            tags=[],
            meta=PromptMetadata(expected_duration="5m"),
            prompt=prompt_text,
            source_file=source_file,
            extracted_by_llm=False,
            fallback_applied=True,
            original_format=self._detect_format(source_file),
        )

    def _generate_name_from_content(self, content: str) -> str:
        """Generate a reasonable name from prompt content.

        Args:
            content: Prompt content

        Returns:
            Generated name
        """
        # Take first line or first 50 characters
        first_line = content.split("\n")[0].strip()
        if first_line and len(first_line) <= 50:
            return first_line

        # Truncate to reasonable length
        return content[:50].strip() + "..." if len(content) > 50 else content.strip()

    def _detect_format(self, source_file: Path | None) -> str:
        """Detect the original format of the prompt.

        Args:
            source_file: Source file path

        Returns:
            Format string
        """
        if not source_file:
            return "text"

        suffix = source_file.suffix.lower()
        if suffix in [".yaml", ".yml"]:
            return "yaml"
        elif suffix == ".md":
            return "markdown"
        else:
            return "text"
