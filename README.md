# PRP-Bench

A benchmarking tool for comparing AI coding CLI tools (Claude Code, Gemini CLI) on standardized coding prompts using isolated git worktrees.

## Quick Start

```bash
# Install dependencies
uv sync

# Set up environment (create .env file with):
# GEMINI_API_KEY=your-gemini-key

# Make sure tools are installed
npm install -g @anthropic-ai/claude-code
npm install -g @google/gemini-cli

# Run benchmarks on both tools
uv run prp-bench-multi prompts/test/hello.md

# Run on specific tool
uv run prp-bench-multi prompts/test/hello.md --tool claude
uv run prp-bench-multi prompts/test/hello.md --tool gemini

# With output file
uv run prp-bench-multi prompts/test/simple-function.prp.yaml -o results.json

# Verbose mode
uv run prp-bench-multi prompts/test/simple-function.prp.yaml -v

# Custom timeout (in seconds)
uv run prp-bench-multi prompts/medium/todo-api.prp.yaml --timeout 180
```

## How It Works

1. **Creates git worktrees** in `tmp/trees/` for isolated execution
2. **Runs AI tools** with auto-approval flags:
   - Claude Code: `--dangerously-skip-permissions`
   - Gemini CLI: `--yolo`
3. **Analyzes results** using git to see what files were created/modified
4. **Compares performance** between tools
5. **Cleans up** worktrees after execution

## Prompt Format

Prompts can be YAML files with metadata:

```yaml
name: "Feature: Add two numbers"
description: "Create a simple addition function"
type: "feature"
complexity: "simple"

prompt: |
  Create a Python function that adds two numbers.
  Include a test file with pytest.
```

Or simple text/markdown files:

```markdown
# Fix Database Connection

The database connection times out under load.
Add connection pooling to fix this issue.
```

## Results

The tool provides:
- **Execution time** for each tool
- **Files created/modified** by each tool
- **Success/failure status**
- **Tool output** (in verbose mode)
- **Side-by-side comparison** when running multiple tools
- **JSON export** for further analysis

Example comparison output:
```
📊 Comparison:
   Claude: 16.1s
   Gemini: 17.3s
   Both created similar files
```

## Supported Tools

### ✅ Claude Code
- Uses `--dangerously-skip-permissions` flag
- No API key needed with max subscription
- Fast execution
- Clean output

### ✅ Gemini CLI  
- Uses `-p` flag for pipeline mode and `--yolo` for auto-approval
- Requires GEMINI_API_KEY in .env file
- ReAct loop provides verbose output
- May run validation automatically

### 🚧 Codex CLI (Coming Soon)
- Will use `--dangerously-auto-approve-everything` flag
- Requires OPENAI_API_KEY

## Next Steps

- Add telemetry collection (OpenTelemetry for Claude, stats parsing for Gemini)
- Support for Codex CLI
- Parallel execution of multiple prompts
- Validation command execution
- Resource usage tracking
- More complex benchmark prompts