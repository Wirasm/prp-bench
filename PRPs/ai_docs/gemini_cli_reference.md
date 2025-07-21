# Google Gemini CLI Reference

## Overview

Google Gemini CLI is an open-source AI agent that brings the power of Gemini directly into your terminal. It uses a reason and act (ReAct) loop with built-in tools and local or remote MCP servers to complete complex coding tasks like bug fixes, feature creation, and test coverage improvement.

## Installation

### Prerequisites
- Node.js version 20 or higher (recommended)
- Google account or API key for authentication

### Installation Methods

```bash
# Method 1: Global NPM installation
npm install -g @google/gemini-cli

# Method 2: Direct execution from GitHub
npx https://github.com/google-gemini/gemini-cli

# Method 3: Docker container
docker run --rm -it us-docker.pkg.dev/gemini-code-dev/gemini-cli/sandbox:0.1.1
```

## Authentication

### 1. Google Account Login (Recommended)
- Default authentication method
- Up to 60 requests per minute
- 1,000 requests per day (free tier)

### 2. Gemini API Key
```bash
# Generate key at Google AI Studio
export GEMINI_API_KEY="YOUR_API_KEY"
# Free tier: 100 requests per day
```

### 3. Vertex AI Authentication
```bash
# Generate key from Google Cloud
export GOOGLE_API_KEY="YOUR_API_KEY"
export GOOGLE_GENAI_USE_VERTEXAI=true
# Free tier with express mode
```

## Basic Usage

### Starting the CLI
```bash
# Launch interactive CLI
gemini

# Start with a specific query
gemini "Write me a Discord bot that answers questions using FAQ.md"

# Working with existing projects
cd existing-project/
gemini "Explain this codebase architecture"
```

### Built-in Commands

| Command | Description |
|---------|-------------|
| `/memory` | Access conversation memory |
| `/stats` | View usage statistics |
| `/tools` | List available tools |
| `/mcp` | Model Context Protocol settings |
| `/` | Discover available commands |

## Core Features

### 1. Large Codebase Query
- Supports up to 1M token context window
- Understands complex project structures
- Maintains context across conversations

### 2. Multimodal Capabilities
- Generate apps from PDFs or sketches
- Process images and diagrams
- Visual code generation

### 3. Automation & Workflow
- Query pull requests
- Handle complex git rebases
- Automate operational tasks

### 4. Tool Integration
- Built-in tools: grep, terminal, file operations
- Web search and web fetch capabilities
- MCP server connections

## Advanced Features

### Model Context Protocol (MCP)
- Connect to local or remote MCP servers
- Extend capabilities with custom tools
- Integration with external services

### Built-in Tools
- **File Operations**: Read, write, edit files
- **Terminal**: Execute shell commands
- **Grep**: Search through codebases
- **Web Search**: Access up-to-date information
- **Web Fetch**: Retrieve web content

### Media Generation
- Integration with Imagen for image generation
- Veo for video generation
- Lyria for audio generation

## Common Use Cases

### Development Tasks
```bash
# Architecture exploration
> Describe the main pieces of this system's architecture.

# Feature implementation
> Implement a first draft for GitHub issue #123.

# Code review and improvement
> Review this pull request and suggest improvements.
```

### Documentation & Reporting
```bash
# Generate documentation
> Create API documentation for this service.

# Project reporting
> Make a slide deck showing git history from the last 7 days.
```

### Bug Fixing & Testing
```bash
# Debug issues
> This function is throwing an error, can you fix it?

# Test coverage
> Add unit tests for the authentication module.
```

## Configuration

### Quota Management
- Quotas are shared between Gemini CLI and Gemini Code Assist agent mode
- Monitor usage with `/stats` command
- Upgrade to higher tiers for increased limits

### Project Setup
- No specific configuration files required
- Works with any project structure
- Integrates with existing development workflows

## Integration Points

### Gemini Code Assist
- Powers VS Code agent mode
- Seamless integration with IDE workflows
- Consistent experience across platforms

### Version Control
- Git integration for commit analysis
- Pull request automation
- Branch management assistance

### CI/CD Workflows
- Automated testing integration
- Deployment assistance
- Pipeline optimization

## Best Practices

### Context Management
- Keep conversations focused on specific topics
- Use clear, specific prompts
- Leverage the 1M token context effectively

### Tool Usage
- Explore available tools with `/tools`
- Use MCP servers for extended functionality
- Combine built-in tools for complex workflows

### Performance Optimization
- Monitor quota usage with `/stats`
- Use appropriate authentication method
- Optimize prompts for better results

## Troubleshooting

### Common Issues
- Node.js version compatibility (requires 20+)
- Authentication configuration
- Quota limitations

### Performance Tips
- Use specific, focused queries
- Leverage built-in tools effectively
- Monitor and manage quota usage

## Development Workflow Examples

### New Project Setup
```bash
cd new-project/
gemini "Set up a Node.js project with TypeScript and Jest"
```

### Code Review
```bash
gemini "Review the changes in this pull request and check for potential issues"
```

### Testing & Quality
```bash
gemini "Add comprehensive unit tests for the user authentication module"
```

## Resources

- Official Documentation: https://developers.google.com/gemini-code-assist/docs/gemini-cli
- GitHub Repository: https://github.com/google-gemini/gemini-cli
- Google AI Studio: https://ai.google.dev/
- Vertex AI Console: https://console.cloud.google.com/vertex-ai

## License & Availability

- Open source (Apache-2.0 license)
- Available for Gemini Code Assist individuals, Standard, and Enterprise editions
- Actively maintained and updated by Google