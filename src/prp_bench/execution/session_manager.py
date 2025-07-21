"""Session management for benchmark runs with Claude Code SDK integration."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from pydantic import BaseModel, Field

from ..models import BenchmarkRun, Prompt, ToolExecutionResult, ToolType


class BenchmarkSession(BaseModel):
    """Represents an active benchmark session."""

    session_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    prompt: Prompt
    tools: list[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = Field(default="created")  # created, running, completed, failed
    results: list[ToolExecutionResult] = Field(default_factory=list)
    worktree_paths: dict[str, str] = Field(default_factory=dict)
    telemetry_enabled: bool = True


class SessionManager:
    """Manages benchmark sessions and their lifecycle."""

    def __init__(self, base_path: Path | None = None):
        """Initialize session manager.

        Args:
            base_path: Base directory for session storage
        """
        from ..config import get_settings

        self.base_path = base_path or Path.cwd()

        # Use consistent directory structure - sessions alongside worktrees
        settings = get_settings()
        base_tmp = self.base_path / settings.worktree.base_dir.parent
        self.sessions_dir = base_tmp / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._active_sessions: dict[str, BenchmarkSession] = {}

    def create_session(
        self, prompt: Prompt, tools: list[str], telemetry_enabled: bool = True
    ) -> BenchmarkSession:
        """Create a new benchmark session.

        Args:
            prompt: Prompt to benchmark
            tools: List of tools to run
            telemetry_enabled: Whether to enable telemetry collection

        Returns:
            Created benchmark session
        """
        session = BenchmarkSession(prompt=prompt, tools=tools, telemetry_enabled=telemetry_enabled)

        # Store session
        self._active_sessions[session.session_id] = session
        self._persist_session(session)

        return session

    def get_session(self, session_id: str) -> BenchmarkSession | None:
        """Get session by ID.

        Args:
            session_id: Session ID to retrieve

        Returns:
            Session if found, None otherwise
        """
        if session_id in self._active_sessions:
            return self._active_sessions[session_id]

        # Try loading from disk
        return self._load_session(session_id)

    def update_session_status(self, session_id: str, status: str) -> None:
        """Update session status.

        Args:
            session_id: Session ID to update
            status: New status (created, running, completed, failed)
        """
        if session_id in self._active_sessions:
            self._active_sessions[session_id].status = status
            self._persist_session(self._active_sessions[session_id])

    def add_result(self, session_id: str, result: ToolExecutionResult) -> None:
        """Add execution result to session.

        Args:
            session_id: Session ID
            result: Tool execution result to add
        """
        if session_id in self._active_sessions:
            self._active_sessions[session_id].results.append(result)
            self._persist_session(self._active_sessions[session_id])

    def set_worktree_path(self, session_id: str, tool: str, path: str) -> None:
        """Set worktree path for a tool in the session.

        Args:
            session_id: Session ID
            tool: Tool name
            path: Worktree path
        """
        if session_id in self._active_sessions:
            self._active_sessions[session_id].worktree_paths[tool] = path
            self._persist_session(self._active_sessions[session_id])

    def get_active_sessions(self) -> list[BenchmarkSession]:
        """Get all active benchmark sessions.

        Returns:
            List of active sessions
        """
        return list(self._active_sessions.values())

    def complete_session(self, session_id: str) -> BenchmarkRun:
        """Mark session as complete and create final benchmark run.

        Args:
            session_id: Session ID to complete

        Returns:
            Final benchmark run with all results
        """
        session = self._active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Update status
        session.status = "completed"

        # Create final benchmark run
        benchmark_run = BenchmarkRun(
            tools=[ToolType(tool) for tool in session.tools],
            prompts=[session.prompt],
            results=session.results,
            total_prompts=1,
            total_executions=len(session.results),
            successful_executions=sum(1 for r in session.results if r.success),
            failed_executions=sum(1 for r in session.results if not r.success),
            completed_at=datetime.now(UTC),
        )

        # Persist final state
        self._persist_session(session)
        self._persist_benchmark_run(session_id, benchmark_run)

        return benchmark_run

    def cleanup_session(self, session_id: str) -> None:
        """Remove session from active sessions.

        Args:
            session_id: Session ID to clean up
        """
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]

        # Remove session file
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()

    def _persist_session(self, session: BenchmarkSession) -> None:
        """Persist session to disk.

        Args:
            session: Session to persist
        """
        session_file = self.sessions_dir / f"{session.session_id}.json"

        with session_file.open("w") as f:
            f.write(session.model_dump_json(indent=2))

    def _load_session(self, session_id: str) -> BenchmarkSession | None:
        """Load session from disk.

        Args:
            session_id: Session ID to load

        Returns:
            Loaded session or None if not found
        """
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return None

        try:
            with session_file.open() as f:
                data = f.read()
                session = BenchmarkSession.model_validate_json(data)
                self._active_sessions[session_id] = session
                return session
        except Exception:
            return None

    def _persist_benchmark_run(self, session_id: str, benchmark_run: BenchmarkRun) -> None:
        """Persist final benchmark run.

        Args:
            session_id: Session ID
            benchmark_run: Final benchmark run to persist
        """
        results_file = self.sessions_dir / f"{session_id}_results.json"

        with results_file.open("w") as f:
            f.write(benchmark_run.model_dump_json(indent=2))

    def list_completed_runs(self) -> list[tuple[str, Path]]:
        """List all completed benchmark runs.

        Returns:
            List of (session_id, results_file_path) tuples
        """
        completed_runs = []

        for results_file in self.sessions_dir.glob("*_results.json"):
            session_id = results_file.stem.replace("_results", "")
            completed_runs.append((session_id, results_file))

        return completed_runs
