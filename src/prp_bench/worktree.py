"""Git worktree management powered by Claude Code SDK."""


from anthropic import Anthropic
from pydantic import BaseModel


class WorktreeSetup(BaseModel):
    """Simple worktree setup configuration."""

    tools: list[str]
    base_dir: str = "tmp/trees"
    run_id: str


class WorktreeManager:
    """Manages worktrees using Claude Code SDK for operations."""

    def __init__(self, anthropic_client: Anthropic | None = None):
        """Initialize with Anthropic client."""
        self.client = anthropic_client or Anthropic()

    def setup_worktrees(self, tools: list[str], run_id: str) -> str:
        """Generate a prompt to set up worktrees for the given tools.

        Args:
            tools: List of tool names (claude, gemini, codex)
            run_id: Unique identifier for this run

        Returns:
            Setup prompt for execution

        """
        return f"""Set up git worktrees for benchmarking run.

## Task
Create separate git worktrees for each AI tool in a temporary directory structure.

## Requirements
1. Create directory: tmp/trees/{run_id}/
2. For each tool in [{", ".join(tools)}]:
   - Create worktree at: tmp/trees/{run_id}/{"{tool}"}/
   - Branch name: benchmark/{"{tool}"}/{run_id}
   - Copy .env file if it exists in the root
## Steps
1. Create the base directory structure
2. Set up git worktrees for each tool
3. Copy environment files
4. Report the created paths

Please execute this setup and report the paths created."""

    def cleanup_worktrees(self, run_id: str) -> str:
        """Generate a prompt to clean up worktrees.

        Args:
            run_id: Run identifier

        Returns:
            Cleanup prompt

        """
        return f"""Clean up git worktrees from benchmarking run.

## Task
Remove all worktrees created for run: {run_id}

## Steps
1. Remove worktrees in tmp/trees/{run_id}/
2. Clean up git worktree references
3. Remove the directory tmp/trees/{run_id}/

Please execute this cleanup."""

    def execute_in_worktree(self, tool: str, run_id: str, prompt_content: str) -> str:
        """Generate a prompt to execute a tool in its worktree.

        Args:
            tool: Tool name
            run_id: Run identifier
            prompt_content: The actual prompt to execute

        Returns:
            Execution prompt

        """
        tool_config = {
            "claude": {"cmd": "claude", "flags": "--dangerously-skip-permissions -p"},
            "gemini": {"cmd": "gemini", "flags": "--yolo"},
            "codex": {
                "cmd": "codex",
                "flags": "exec --dangerously-auto-approve-everything",
            },
        }

        config = tool_config.get(tool, {})

        return f"""Execute {tool} in its worktree.

## Task
Run {tool} with the provided prompt in its isolated worktree.

## Setup
1. Change to worktree: tmp/trees/{run_id}/{tool}/
2. Save the prompt content to a file: prompt.txt
3. Execute the tool with appropriate flags

## Prompt Content
```
{prompt_content}
```

## Execution Command
```bash
cd tmp/trees/{run_id}/{tool}/
echo '{prompt_content}' > prompt.txt
{config.get("cmd", tool)} {config.get("flags", "")} "$(cat prompt.txt)"
```

## Capture
- Start time
- Tool output (stdout/stderr)
- Exit code
- End time
- Any files created or modified

Please execute and report results."""

    def analyze_results(self, tool: str, run_id: str) -> str:
        """Generate a prompt to analyze execution results.

        Args:
            tool: Tool name
            run_id: Run identifier

        Returns:
            Analysis prompt

        """
        return f"""Analyze the results of {tool} execution.

## Task
Examine what {tool} did in its worktree and extract metrics.

## Location
tmp/trees/{run_id}/{tool}/

## Analysis Steps
1. Run git diff to see all changes
2. Count files created/modified
3. Count lines added/removed
4. List all new files
5. Check if any tests were created
6. Run any validation commands if specified

## Report
- Files changed
- Lines of code metrics
- Test coverage if applicable
- Any errors encountered
- Overall success/failure

Please analyze and report findings."""
