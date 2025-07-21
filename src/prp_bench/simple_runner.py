"""Simple runner focused on Claude Code only."""

import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml


class ClaudeCodeRunner:
    """Simple runner for Claude Code benchmarking."""

    def __init__(self, base_path: Path | None = None, timeout_seconds: int = 300) -> None:
        """Initialize ClaudeCodeRunner.

        Args:
            base_path: Base path for operations
            timeout_seconds: Timeout for operations
        """
        self.base_path = base_path or Path.cwd()
        self.tmp_dir = self.base_path / "tmp" / "trees"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds  # Default 5 minutes

    def run_prompt(self, prompt_file: Path, cleanup: bool = False) -> dict:
        """Run a single prompt with Claude Code.

        Args:
            prompt_file: Path to prompt file
            cleanup: Whether to cleanup worktree after execution

        Returns:
            Dictionary with execution results

        """
        run_id = str(uuid4())[:8]
        worktree_dir = self.tmp_dir / f"claude-{run_id}"

        # Load prompt
        if prompt_file.suffix in [".yaml", ".yml"]:
            with prompt_file.open() as f:
                prompt_data = yaml.safe_load(f)
            prompt_content = prompt_data.get("prompt", "")
        else:
            prompt_content = prompt_file.read_text()

        # Setup worktree
        # Setting up worktree
        self._setup_worktree(worktree_dir, run_id)

        try:
            # Execute Claude Code
            # Executing Claude Code
            start_time = datetime.now(UTC)

            result = self._execute_claude(worktree_dir, prompt_content)

            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            # Analyze results
            # Analyzing results
            analysis = self._analyze_results(worktree_dir)

            result_data = {
                "tool": "claude",
                "prompt_file": str(prompt_file),
                "run_id": run_id,
                "success": result["success"],
                "duration_seconds": duration,
                "output": result["output"],
                "error": result.get("error"),
                "analysis": analysis,
                "timestamp": start_time.isoformat(),
            }
            
            # Always include worktree path (useful for inspection)
            result_data["worktree_path"] = str(worktree_dir)
                
            return result_data

        finally:
            # Cleanup
            if cleanup:
                # Cleaning up worktree
                self._cleanup_worktree(worktree_dir)

    def _setup_worktree(self, worktree_dir: Path, run_id: str) -> None:
        """Set up a git worktree."""
        branch_name = f"benchmark/claude/{run_id}"

        # Create worktree
        cmd = ["git", "worktree", "add", "-b", branch_name, str(worktree_dir)]
        subprocess.run(cmd, cwd=self.base_path, check=True, capture_output=True)

        # Copy .env if exists
        env_file = self.base_path / ".env"
        if env_file.exists():
            import shutil

            shutil.copy2(env_file, worktree_dir / ".env")

    def _execute_claude(self, worktree_dir: Path, prompt: str) -> dict[str, Any]:
        """Execute Claude Code with the prompt."""
        # Save prompt to file
        prompt_file = worktree_dir / "prompt.txt"
        prompt_file.write_text(prompt)

        # Load environment variables from .env if it exists
        import os

        env = os.environ.copy()

        # Set Claude timeout environment variables
        env["BASH_DEFAULT_TIMEOUT_MS"] = str(self.timeout_seconds * 1000)
        env["BASH_MAX_TIMEOUT_MS"] = str(self.timeout_seconds * 1000)

        # Execute Claude
        cmd = ["claude", "--dangerously-skip-permissions", "-p", prompt]

        try:
            result = subprocess.run(
                cmd,
                check=False, cwd=worktree_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=env,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Execution timed out after {self.timeout_seconds} seconds",
            }
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}

    def _analyze_results(self, worktree_dir: Path) -> dict[str, Any]:
        """Analyze what Claude Code did."""
        analysis: dict[str, Any] = {
            "files_created": [],
            "files_modified": [],
            "git_status": "",
            "git_diff_stats": "",
        }

        # Get git status
        try:
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                check=False, cwd=worktree_dir,
                capture_output=True,
                text=True,
            )
            analysis["git_status"] = status.stdout

            # Parse status for created/modified files
            for line in status.stdout.splitlines():
                if line.startswith("??"):
                    analysis["files_created"].append(line[3:])
                elif line.startswith((" M", "M ")):
                    analysis["files_modified"].append(line[3:])

            # Get diff stats
            diff = subprocess.run(
                ["git", "diff", "--stat"],
                check=False, cwd=worktree_dir,
                capture_output=True,
                text=True,
            )
            analysis["git_diff_stats"] = diff.stdout

        except Exception as e:
            analysis["error"] = str(e)

        return analysis

    def _cleanup_worktree(self, worktree_dir: Path) -> None:
        """Remove the worktree."""
        try:
            # Remove worktree
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_dir), "--force"],
                check=False, cwd=self.base_path,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            # If git fails, try manual removal
            import shutil

            if worktree_dir.exists():
                shutil.rmtree(worktree_dir)

        # Prune worktree refs
        subprocess.run(
            ["git", "worktree", "prune"], check=False, cwd=self.base_path, capture_output=True,
        )
