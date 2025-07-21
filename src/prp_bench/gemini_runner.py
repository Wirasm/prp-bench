"""Gemini CLI runner for benchmarking."""

import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml


class GeminiRunner:
    """Runner for Google Gemini CLI benchmarking."""

    def __init__(self, base_path: Path | None = None, timeout_seconds: int = 600) -> None:
        """Initialize GeminiRunner.

        Args:
            base_path: Base path for operations
            timeout_seconds: Timeout for operations
        """
        self.base_path = base_path or Path.cwd()
        self.tmp_dir = self.base_path / "tmp" / "trees"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds  # Default 10 minutes

    def run_prompt(self, prompt_file: Path, cleanup: bool = False) -> dict:
        """Run a single prompt with Gemini CLI.

        Args:
            prompt_file: Path to prompt file
            cleanup: Whether to cleanup worktree after execution

        Returns:
            Dictionary with execution results

        """
        run_id = str(uuid4())[:8]
        worktree_dir = self.tmp_dir / f"gemini-{run_id}"

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
            # Execute Gemini CLI
            # Executing Gemini CLI
            start_time = datetime.now(UTC)

            result = self._execute_gemini(worktree_dir, prompt_content)

            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            # Analyze results
            # Analyzing results
            analysis = self._analyze_results(worktree_dir)

            return {
                "tool": "gemini",
                "prompt_file": str(prompt_file),
                "run_id": run_id,
                "success": result["success"],
                "duration_seconds": duration,
                "worktree_path": str(worktree_dir),
                "output": result["output"],
                "error": result.get("error"),
                "analysis": analysis,
                "timestamp": start_time.isoformat(),
            }

        finally:
            # Cleanup
            if cleanup:
                # Cleaning up worktree
                self._cleanup_worktree(worktree_dir)

    def _setup_worktree(self, worktree_dir: Path, run_id: str) -> None:
        """Set up a git worktree."""
        branch_name = f"benchmark/gemini/{run_id}"

        # Create worktree
        cmd = ["git", "worktree", "add", "-b", branch_name, str(worktree_dir)]
        subprocess.run(cmd, cwd=self.base_path, check=True, capture_output=True)

        # Copy .env if exists
        env_file = self.base_path / ".env"
        if env_file.exists():
            import shutil

            shutil.copy2(env_file, worktree_dir / ".env")

    def _execute_gemini(self, worktree_dir: Path, prompt: str) -> dict[str, Any]:
        """Execute Gemini CLI with the prompt.

        Uses -p flag for non-interactive mode and --yolo for auto-approval.
        """
        # Save prompt to file for reference
        prompt_file = worktree_dir / "prompt.txt"
        prompt_file.write_text(prompt)

        # Load environment variables from .env if it exists
        import os

        env = os.environ.copy()
        env_file = worktree_dir / ".env"
        if env_file.exists():
            # Simple .env parsing
            with env_file.open() as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env[key.strip()] = value.strip()

        # Execute Gemini with pipeline mode and YOLO
        cmd = ["gemini", "-p", prompt, "--yolo"]

        # Add debug flag if we want more verbose output

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
        """Analyze what Gemini CLI did."""
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
