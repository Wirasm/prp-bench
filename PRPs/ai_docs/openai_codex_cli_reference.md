# OpenAI Codex CLI Reference

## Overview

OpenAI Codex CLI is an open-source command-line tool that brings the power of OpenAI's latest reasoning models directly to your terminal. It acts as a lightweight coding agent that can read, modify, and run code on your local machine to help build features faster, fix bugs, and understand unfamiliar code.

**Note**: The original OpenAI Codex model was deprecated in March 2023, but the CLI tool continues development using newer models like o4-mini and o3.

## Installation

### Prerequisites
- macOS 12+, Ubuntu 20.04+/Debian 10+, Windows via WSL2
- Node.js 22 or newer
- 4-8 GB RAM recommended
- Git 2.23+ (optional)

### Installation Methods

```bash
# Method 1: NPM (Primary)
npm install -g @openai/codex

# Method 2: Homebrew
brew install codex

# Method 3: Direct binary download
# Download from GitHub Releases page
```

## Authentication

### API Key Setup
```bash
# Export OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
```

### ChatGPT Pro Users
```bash
# Login for Pro subscribers
codex login
```

### Pricing
- **ChatGPT Pro**: $200/month (includes Codex access)
- **API Usage**: $1.50/1M input tokens, $6/1M output tokens
- **Prompt Caching**: 75% discount on cached prompts

## Basic Commands

### Interactive Mode
```bash
# Start interactive REPL
codex

# Run with initial prompt
codex "explain this codebase to me"

# Execute specific task
codex exec "create a todo app"
```

### Key Flags

| Flag | Description |
|------|-------------|
| `--model/-m` | Select specific AI model (default: o4-mini) |
| `--ask-for-approval/-a` | Configure approval settings |
| `--full-auto` | Enable automatic execution mode |
| `--suggest` | Suggest mode (default) |
| `--auto-edit` | Auto-edit mode |
| `--config` | Override config file |
| `--quiet/-q` | Non-interactive mode |
| `--upgrade` | Update to latest version |

### Model Selection
```bash
# Use default model (o4-mini)
codex

# Use specific model
codex -m o3

# Available models: o4-mini, o3, gpt-4, gpt-3.5-turbo
```

## Operating Modes

### 1. Suggest Mode (Default)
- Provides suggestions without making changes
- Requires manual approval for actions
- Safest mode for exploration

### 2. Auto-Edit Mode
- Automatically edits files based on suggestions
- Asks for approval before major changes
- Balanced automation level

### 3. Full-Auto Mode
- Executes tasks with minimal human intervention
- Suitable for well-defined tasks
- Requires careful prompt engineering

```bash
# Switch modes during session
/mode suggest
/mode auto-edit
/mode full-auto
```

## Core Features

### 1. Multimodal Input
- Process text, screenshots, and diagrams
- Generate code from visual specifications
- Understand complex visual contexts

### 2. Local Execution
- Sandboxed execution environment
- Network and file system restrictions
- Source code stays local

### 3. Rich Approval Workflow
- Three distinct approval modes
- Configurable automation levels
- Safety-first design

### 4. Chat-Driven Development
- Natural language interaction
- Context-aware conversations
- Iterative development support

## Configuration

### Default Config Location
```bash
~/.codex/config.toml
```

### Custom Configuration
```bash
# Use custom config file
codex --config /path/to/config.toml
```

### Environment Variables
```bash
# Required
export OPENAI_API_KEY="your-key"

# Optional
export CODEX_MODEL="o4-mini"
export CODEX_APPROVAL_MODE="suggest"
```

## Security Model

### Sandboxed Execution
- Isolated execution environment
- Limited network access
- Configurable file system permissions

### Approval Policies
- Configurable approval requirements
- Action-based permission system
- Safe defaults with manual override

### Data Privacy
- Local code processing
- No data transmission without approval
- Transparent operation logging

## Common Use Cases

### Code Exploration
```bash
# Understand codebase structure
codex "explain the architecture of this project"

# Analyze specific functions
codex "what does this function do?"
```

### Feature Development
```bash
# Create new features
codex "add user authentication to this app"

# Implement specific functionality
codex "create a REST API for user management"
```

### Bug Fixing
```bash
# Debug issues
codex "fix this error: [paste error message]"

# Code review
codex "review this pull request for potential issues"
```

### Documentation
```bash
# Generate documentation
codex "create API documentation for this service"

# Add code comments
codex "add comprehensive comments to this module"
```

## Alternative: Open Codex

### Community Fork Features
- Multiple AI provider support (OpenAI, Gemini, OpenRouter, Ollama)
- Fully local operation
- Extended customization options

### Installation
```bash
npm install -g open-codex
```

### Usage
```bash
# Interactive mode
open-codex

# With specific provider
open-codex --provider gemini

# Full auto mode
open-codex --approval-mode full-auto "create a todo app"
```

## Best Practices

### Prompt Engineering
- Be specific about requirements
- Provide context about existing code
- Use clear, actionable language

### Safety Considerations
- Start with suggest mode
- Review all changes before approval
- Test in isolated environments

### Performance Optimization
- Use appropriate model for task complexity
- Leverage prompt caching for repeated operations
- Monitor API usage and costs

## Integration Examples

### Git Workflow
```bash
# Automated commit messages
codex "generate commit message for these changes"

# Code review assistance
codex "review this diff and suggest improvements"
```

### Testing Integration
```bash
# Generate test cases
codex "create unit tests for this module"

# Fix failing tests
codex "fix these failing test cases"
```

### Documentation Workflow
```bash
# API documentation
codex "generate OpenAPI spec for this service"

# README generation
codex "create comprehensive README for this project"
```

## Troubleshooting

### Common Issues
- API key configuration
- Model availability
- Permission settings
- Network connectivity

### Performance Issues
- Model selection optimization
- Context window management
- Approval workflow tuning

### Debugging
- Enable verbose logging
- Check configuration files
- Verify API key permissions

## Migration from Legacy Codex

### Key Changes
- Original Codex model deprecated (March 2023)
- New models: o4-mini, o3
- Enhanced multimodal capabilities
- Improved safety features

### Update Process
```bash
# Update to latest version
codex --upgrade

# Verify installation
codex --version
```

## Resources

- Official Documentation: https://help.openai.com/en/articles/11096431-openai-codex-cli-getting-started
- GitHub Repository: https://github.com/openai/codex
- Open Codex Fork: https://github.com/ymichael/open-codex
- OpenAI Platform: https://platform.openai.com/docs/
- API Documentation: https://platform.openai.com/docs/api-reference

## License & Support

- Open source (Apache-2.0 license)
- Active community development
- Regular updates and improvements
- Enterprise support available through OpenAI