# Claude Code CLI Reference

## Overview

Claude Code is Anthropic's official CLI for agentic coding that lives in your terminal. It understands your codebase and helps you code faster by executing routine tasks, explaining complex code, and handling git workflows through natural language commands.

## Installation

```bash
# Prerequisites: Node.js 18 or newer
npm install -g @anthropic-ai/claude-code
```

## Core Commands

### Basic Usage
```bash
# Start interactive REPL
claude

# Start REPL with initial prompt
claude "query"

# Query via SDK and exit (headless mode)
claude -p "query"

# Continue most recent conversation
claude -c

# Resume specific session
claude -r "<session-id>" "query"

# Update to latest version
claude update

# Configure Model Context Protocol servers
claude mcp
```

### Key CLI Flags

| Flag | Description |
|------|-------------|
| `--add-dir` | Add working directories |
| `--allowedTools` | Specify permitted tools |
| `--print/-p` | Print response without interactive mode |
| `--output-format` | Set response format (text/json/stream-json) |
| `--verbose` | Enable detailed logging |
| `--max-turns` | Limit agentic turns |
| `--model` | Set specific model |
| `--permission-mode` | Set permission mode |
| `--continue` | Load most recent conversation |
| `--dangerously-skip-permissions` | Skip permission checks |

### Advanced Usage

```bash
# Unix-style piping
cat file.txt | claude -p "explain this code"

# Session management
claude new  # Start new session with clean context
claude resume  # Resume last session with context

# Project initialization
claude init  # Create CLAUDE.md file for project memory
```

## Core Features

### 1. Build Features from Descriptions
- Tell Claude what you want to build in plain English
- It will make a plan, write the code, and ensure it works

### 2. Debug and Fix Issues
- Describe a bug or paste an error message
- Claude analyzes your codebase, identifies problems, and implements fixes

### 3. Navigate Any Codebase
- Ask anything about your team's codebase
- Get thoughtful answers back with context

### 4. Takes Direct Action
- Directly edit files
- Run commands
- Create commits

## Project Configuration

### CLAUDE.md Files
Create a `CLAUDE.md` file in your project root to provide context:

```markdown
# Project Context
## Architecture
- Frontend: React with TypeScript
- Backend: Node.js with Express
- Database: PostgreSQL

## Commands
- `npm run build`: Build the project
- `npm run test`: Run tests
- `npm run typecheck`: Type checking

## Code Style
- Use ES modules (import/export)
- Destructure imports when possible
- Always use TypeScript strict mode

## Workflow
- Run typecheck after code changes
- Prefer single test runs for performance
```

### Custom Slash Commands
Create markdown files in `.claude/commands/` to define custom slash commands:

```bash
# Example: .claude/commands/test.md
# Run all unit tests and report results
npm run test
```

Usage: `/test` will execute your custom command

## Advanced Features

### Model Context Protocol (MCP)
- Connect to external data sources
- Integrates with development tools
- Supports composable workflows

### Sub-agent Pattern
Use the Task tool for complex problems:
```bash
# MCP server usage
claude mcp serve
```

### Headless Mode
```bash
# Integrate programmatically
claude -p "task description"
```

## Best Practices

### Context Management
- Use `/clear` frequently for better results
- Create new sessions for different topics
- Keep CLAUDE.md files concise and human-readable

### Security
- Direct API connection (no intermediate servers)
- Tiered permission system
- Context stays local unless explicitly shared

### Performance Tips
- Use specific file paths when possible
- Leverage project-specific CLAUDE.md files
- Break complex tasks into smaller steps

## Common Workflows

### Development Cycle
1. Navigate to project: `cd your-project`
2. Start Claude: `claude`
3. Ask for help: "Help me implement user authentication"
4. Review and approve changes
5. Test and iterate

### Bug Fixing
1. Describe the bug or paste error message
2. Claude analyzes codebase and identifies issue
3. Claude implements fix
4. Verify the solution works

### Code Exploration
1. Ask about architecture: "Explain this codebase structure"
2. Query specific functionality: "How does authentication work?"
3. Get implementation details: "Show me the user model"

## Integration Points

### Git Workflows
- Automatic commit creation
- Branch management
- Code review assistance

### CI/CD Integration
- GitHub Actions compatibility
- Automated testing workflows
- Deployment automation

### Development Tools
- VS Code integration
- Terminal workflows
- Unix piping support

## Troubleshooting

### Common Issues
- Node.js version compatibility (requires 18+)
- API key configuration
- Permission settings

### Performance
- Use `/clear` for conversation cleanup
- Manage context window size
- Optimize for specific tasks

## Resources

- Official Documentation: https://docs.anthropic.com/en/docs/claude-code
- GitHub Repository: https://github.com/anthropics/claude-code
- Community Resources: https://github.com/hesreallyhim/awesome-claude-code