# PRP-Bench Implementation Summary

## What We Built

A benchmarking tool for AI coding CLI tools that compares Claude Code and Gemini CLI. The tool executes prompts in isolated git worktrees and collects performance metrics.

## Current Features

### ✅ Implemented
- **Claude Code Integration**: Full support with `--dangerously-skip-permissions` flag
- **Gemini CLI Integration**: Full support with `-p` and `--yolo` flags  
- **Multi-Tool Comparison**: Run benchmarks on both tools and compare results
- **Git Worktree Isolation**: Each execution runs in its own worktree under `tmp/trees/`
- **Prompt Formats**: Support for both YAML and plain text/markdown prompts
- **Result Analysis**: Git status parsing to track files created/modified
- **JSON Output**: Save individual or comparison results
- **Environment Variable Support**: Loads API keys from .env file
- **Configurable Timeouts**: Custom timeout settings for each tool (defaults: Claude=300s, Gemini=600s)

### 🏗️ Architecture
```
src/prp_bench/
├── simple_runner.py    # Claude Code execution logic
├── gemini_runner.py    # Gemini CLI execution logic
├── simple_cli.py       # Claude-only CLI
├── multi_cli.py        # Multi-tool CLI for comparisons
├── models.py          # Data models (prepared for full implementation)
├── worktree.py        # Worktree management (using Claude SDK approach)
├── runner.py          # Full runner (ready for multi-tool support)
└── main.py            # Main CLI (ready for multi-tool support)
```

## Usage

```bash
# Compare both tools
uv run prp-bench-multi prompts/test/hello.md

# Run specific tool
uv run prp-bench-multi prompts/test/hello.md --tool claude
uv run prp-bench-multi prompts/test/hello.md --tool gemini

# With verbose output
uv run prp-bench-multi prompts/test/simple-function.prp.yaml -v

# Save comparison results to JSON
uv run prp-bench-multi prompts/test/hello.md -o comparison.json
```

## Example Output

```json
{
  "tool": "claude",
  "prompt_file": "prompts/test/hello.md",
  "run_id": "1cc44006",
  "success": true,
  "duration_seconds": 8.91201,
  "files_created": ["hello.py"],
  "git_status": "?? hello.py\n"
}
```

## Next Steps

1. **Add Telemetry Collection**
   - Set up OpenTelemetry collector
   - Parse Claude Code metrics
   - Add to result output

2. **Add Validation Execution**
   - Run validation commands from prompt
   - Capture validation results
   - Include in success determination

3. **Add Other Tools**
   - Implement Gemini CLI runner
   - Implement Codex CLI runner
   - Unified result comparison

4. **Enhance Metrics**
   - Token usage tracking
   - Cost estimation
   - Resource monitoring

5. **Parallel Execution**
   - Run multiple prompts in parallel
   - Compare tools side-by-side
   - Aggregate results

## Key Findings from Comparison

### Performance
- **Claude Code**: Generally consistent execution times (9-61s depending on complexity)
- **Gemini CLI**: Can be faster on complex tasks (44s vs 61s for TODO API), more verbose output
- Both tools successfully complete the same tasks with similar quality

### Behavioral Differences
- **Claude**: Clean, concise output focused on what was done
- **Gemini**: ReAct loop shows thinking process, may run validation automatically
- **File Creation**: Both create the same core files, Gemini may create additional artifacts (e.g., __pycache__, venv/)
- **Dependencies**: Gemini often creates virtual environments and installs dependencies automatically

### Integration Complexity
- **Claude**: Simple execution model with direct output
- **Gemini**: Pipeline mode (`-p`) works well, YOLO mode enables automation

## Key Design Decisions

1. **Git Worktrees**: Provides complete isolation between runs
2. **Multi-Tool Support**: Unified interface for comparing different tools
3. **Environment Variables**: Clean API key management via .env
4. **Simple Git-Based Analysis**: Rely on git status/diff for tracking changes
5. **Modular Architecture**: Easy to add new tools by creating new runner classes