# PRP-Bench Execution Strategy

## Overview

PRP-Bench executes AI coding tools in isolated git worktrees to ensure clean, non-interfering environments for each tool's execution.

## Worktree-Based Isolation

### Why Worktrees?

1. **Complete Isolation**: Each AI tool operates in its own working directory
2. **Parallel Execution**: Tools can run simultaneously without conflicts
3. **Clean State**: Each execution starts from a known git state
4. **Easy Cleanup**: Worktrees can be removed without affecting the main repo
5. **Realistic Testing**: Simulates real-world usage where tools work on separate branches

### Worktree Structure

```
prp-bench/                    # Main repository
├── .git/                     # Git directory
├── src/                      # Benchmarking tool source
└── .worktrees/               # Isolated execution environments
    ├── claude-code-001/      # Worktree for Claude Code execution
    ├── gemini-001/           # Worktree for Gemini CLI execution
    └── codex-001/            # Worktree for Codex CLI execution
```

## Execution Flow

### 1. Setup Phase
```python
# For each AI tool and prompt:
1. Create worktree: git worktree add .worktrees/{tool}-{run_id}
2. Copy prompt file to worktree
3. Setup tool-specific environment (API keys, config)
4. Initialize telemetry collection
```

### 2. Execution Phase
```python
# In each worktree:
1. Change to worktree directory
2. Execute AI tool with prompt:
   - Claude: claude -p "$(cat prompt.prp)" --dangerously-skip-permissions
   - Gemini: gemini "$(cat prompt.prp)"
   - Codex: codex exec "$(cat prompt.prp)" --full-auto
3. Capture output, errors, and telemetry
4. Monitor resource usage
```

### 3. Validation Phase
```python
# Run validation commands from PRP:
1. Syntax checks (ruff, mypy)
2. Unit tests (pytest)
3. Integration tests
4. Custom validation scripts
5. Capture validation results
```

### 4. Collection Phase
```python
# Gather results:
1. Git diff to see changes made
2. Collect telemetry data:
   - Claude: OpenTelemetry metrics
   - Gemini: Parse stats output
   - Codex: Process logs
3. Archive outputs
4. Calculate metrics
```

### 5. Cleanup Phase
```python
# Clean up worktrees:
1. Save artifacts if needed
2. Remove worktree: git worktree remove {path}
3. Prune worktree references
```

## Implementation Details

### WorktreeManager Class

```python
class WorktreeManager:
    """Manages git worktrees for isolated execution."""
    
    def create_worktree(self, tool_name: str, run_id: str) -> Path:
        """Create a new worktree for execution."""
        
    def setup_environment(self, worktree_path: Path, tool: str):
        """Configure tool-specific environment."""
        
    def cleanup_worktree(self, worktree_path: Path):
        """Remove worktree after execution."""
```

### Execution Runner

```python
class ExecutionRunner:
    """Orchestrates tool execution in worktrees."""
    
    async def run_prompt(
        self,
        prompt: Prompt,
        tools: List[str],
        parallel: bool = True
    ) -> BenchmarkResults:
        """Execute prompt across specified tools."""
```

## Telemetry Collection

### Claude Code (OpenTelemetry)
```bash
# Environment setup in worktree
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

### Gemini CLI
```python
# Parse output from /stats command
gemini_stats = parse_gemini_stats(output)
```

### Codex CLI
```python
# Capture process metrics and parse logs
codex_metrics = extract_codex_metrics(logs)
```

## Parallel Execution

### Process Pool
```python
async def execute_parallel(prompts: List[Prompt], tools: List[str]):
    """Execute multiple prompts across tools in parallel."""
    with ProcessPoolExecutor(max_workers=len(tools)) as executor:
        futures = []
        for tool in tools:
            worktree = create_worktree(tool)
            future = executor.submit(run_in_worktree, worktree, tool, prompt)
            futures.append(future)
        
        results = await asyncio.gather(*futures)
```

## Error Handling

### Failure Modes
1. **Tool Installation**: Verify tool is installed before execution
2. **API Key Issues**: Validate authentication before starting
3. **Worktree Conflicts**: Handle existing worktree names
4. **Resource Limits**: Monitor and enforce memory/CPU limits
5. **Timeout**: Kill long-running executions

### Recovery Strategy
```python
try:
    result = await run_tool_in_worktree(tool, prompt)
except ToolExecutionError as e:
    # Log error, clean up worktree
    # Mark as failed in results
    # Continue with other tools
```

## Resource Management

### Limits per Execution
- **CPU**: Limited to 2 cores per tool
- **Memory**: 4GB limit per process
- **Disk**: 1GB limit for changes
- **Time**: 30-minute timeout (configurable)

### Monitoring
```python
class ResourceMonitor:
    """Monitor resource usage during execution."""
    
    def start_monitoring(self, pid: int):
        """Begin tracking process resources."""
        
    def get_metrics(self) -> ResourceMetrics:
        """Return CPU, memory, disk usage."""
```

## Security Considerations

1. **API Key Isolation**: Each worktree gets only its required keys
2. **File System Access**: Restrict to worktree directory
3. **Network Access**: Monitor and log all network requests
4. **Process Isolation**: Use subprocess with limited permissions

## Example Execution

```bash
# Simple execution
prp-bench run prompts/simple/fix-bug.prp.yaml

# Parallel execution of multiple prompts
prp-bench run prompts/medium/*.prp.yaml --parallel

# Specific tools only
prp-bench run prompts/complex/refactor.prp.yaml --tools claude,gemini

# With resource limits
prp-bench run prompts/heavy/generate-sdk.prp.yaml --memory-limit 8G --timeout 60m
```

## Metrics Collected

Per execution:
- **Duration**: Total time, execution time, validation time
- **Tokens**: Input/output tokens used
- **Cost**: Estimated cost based on pricing
- **Changes**: Files created/modified, lines added/removed
- **Validation**: Pass/fail for each validation step
- **Resources**: Peak CPU, memory, disk usage
- **Errors**: Any errors or warnings encountered