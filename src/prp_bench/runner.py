"""Main execution runner using Claude Code SDK."""

import json
from datetime import datetime
from uuid import uuid4

from anthropic import Anthropic

from .models import BenchmarkRun, Prompt, ToolExecutionResult, ToolType
from .worktree import WorktreeManager


class BenchmarkRunner:
    """Orchestrates benchmark execution using Claude Code SDK."""

    def __init__(self, anthropic_client: Anthropic | None = None):
        """Initialize runner with Anthropic client."""
        self.client = anthropic_client or Anthropic()
        self.worktree_manager = WorktreeManager(self.client)

    async def run_benchmark(
        self, prompts: list[Prompt], tools: list[str] | None = None,
    ) -> BenchmarkRun:
        """Run benchmark across tools and prompts.

        Args:
            prompts: List of prompts to execute
            tools: List of tool names to benchmark

        Returns:
            BenchmarkRun with results

        """
        if tools is None:
            tools = ["claude", "gemini", "codex"]
        run_id = str(uuid4())[:8]
        benchmark_run = BenchmarkRun(
            tools=[ToolType(t) for t in tools],
            prompts=prompts,
            total_prompts=len(prompts),
        )

        # Setup worktrees
        setup_prompt = self.worktree_manager.setup_worktrees(tools, run_id)
        setup_response = await self._execute_with_claude(setup_prompt)
        print(f"Worktrees setup: {setup_response}")

        # Execute each prompt on each tool
        for prompt in prompts:
            for tool in tools:
                result = await self._execute_prompt_on_tool(tool, prompt, run_id)
                benchmark_run.add_result(result)

        # Cleanup worktrees
        cleanup_prompt = self.worktree_manager.cleanup_worktrees(run_id)
        cleanup_response = await self._execute_with_claude(cleanup_prompt)
        print(f"Cleanup complete: {cleanup_response}")

        benchmark_run.completed_at = datetime.now()
        return benchmark_run

    async def _execute_prompt_on_tool(
        self, tool: str, prompt: Prompt, run_id: str,
    ) -> ToolExecutionResult:
        """Execute a single prompt on a single tool.

        Args:
            tool: Tool name
            prompt: Prompt to execute
            run_id: Run identifier

        Returns:
            Execution result

        """
        # Generate execution prompt
        exec_prompt = self.worktree_manager.execute_in_worktree(
            tool, run_id, prompt.prompt,
        )

        # Execute via Claude
        exec_response = await self._execute_with_claude(exec_prompt)

        # Analyze results
        analysis_prompt = self.worktree_manager.analyze_results(tool, run_id)
        analysis_response = await self._execute_with_claude(analysis_prompt)

        # Parse results using Claude
        parse_prompt = f"""Parse the following execution results into structured data.

## Execution Output
{exec_response}

## Analysis Output
{analysis_response}

## Extract
- Success: true/false
- Files created: list
- Files modified: list
- Lines added: number
- Lines removed: number
- Errors: any error messages
- Duration: execution time

Return as JSON."""

        parsed_response = await self._execute_with_claude(parse_prompt)

        try:
            parsed_data = json.loads(parsed_response)
        except json.JSONDecodeError:
            parsed_data = {"success": False, "error": "Failed to parse results"}

        # Create result object
        from .models import ExecutionTiming

        result = ToolExecutionResult(
            tool=ToolType(tool),
            prompt_id=prompt.prompt_id,
            success=parsed_data.get("success", False),
            timing=ExecutionTiming(start_time=datetime.now()),  # Simplified for now
            stdout=exec_response,
            error=parsed_data.get("error"),
        )

        return result

    async def _execute_with_claude(self, prompt: str) -> str:
        """Execute a prompt using Claude Code SDK.

        Args:
            prompt: Prompt to execute

        Returns:
            Response from Claude

        """
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )

        # Handle different content types from Anthropic API
        content = response.content[0]
        if hasattr(content, "text"):
            return content.text
        return str(content)
