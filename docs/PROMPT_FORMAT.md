# PRP-Bench Prompt Format

## Overview

PRP-Bench uses a simplified version of the PRP (Prompt Request Protocol) format, optimized for benchmarking AI coding CLI tools. This format is designed to work with real-world prompts like JIRA tasks, user stories, or GitHub issues.

## Prompt File Structure

```yaml
# prompt.prp.yaml
name: "Feature: Add user authentication"
description: "Implement JWT-based authentication system"
type: "feature" # feature, bug, refactor, test, docs
complexity: "medium" # simple, medium, complex
tags: ["auth", "security", "api"]

# Metadata for benchmarking
meta:
  expected_duration: "30m"
  expected_loc: 500
  validation_required: true

# The actual prompt content
prompt: |
  ## Goal
  Implement JWT-based authentication for the REST API with refresh tokens.
  
  ## Requirements
  - User registration endpoint
  - Login endpoint returning access + refresh tokens
  - Token refresh endpoint
  - Protected endpoint decorator
  - Secure password hashing (bcrypt)
  
  ## Technical Details
  - Use PyJWT for token generation
  - Access tokens expire in 15 minutes
  - Refresh tokens expire in 7 days
  - Store refresh tokens in database

# Optional: Provide context files
context:
  files:
    - path: "src/models/user.py"
      why: "Existing user model to extend"
    - path: "src/api/routes.py"
      why: "API structure to follow"
  
  urls:
    - url: "https://pyjwt.readthedocs.io/en/stable/"
      why: "JWT library documentation"

# Validation commands to verify success
validation:
  syntax:
    - "ruff check src/"
    - "mypy src/"
  
  tests:
    - "pytest tests/test_auth.py -v"
  
  integration:
    - description: "Test registration endpoint"
      command: |
        curl -X POST http://localhost:8000/auth/register \
          -H "Content-Type: application/json" \
          -d '{"email": "test@example.com", "password": "secure123"}'
      expected: "201"

# Expected outcomes for benchmarking
expected_outcomes:
  files_created:
    - "src/auth/jwt_handler.py"
    - "src/auth/routes.py"
    - "tests/test_auth.py"
  
  files_modified:
    - "src/models/user.py"
    - "src/api/routes.py"
  
  capabilities:
    - "User can register"
    - "User can login and receive tokens"
    - "User can refresh access token"
    - "Protected endpoints reject invalid tokens"
```

## Simplified Text Format

For simpler prompts (like JIRA tasks), we support plain markdown:

```markdown
# Fix: Database connection timeout

## Problem
The application crashes with timeout errors when connecting to PostgreSQL under high load.

## Expected Solution
- Implement connection pooling
- Add retry logic with exponential backoff
- Proper error handling and logging

## Validation
- No timeout errors under load test (100 concurrent connections)
- All existing tests pass
```

## Directory Structure

```
prompts/
├── simple/           # Simple bug fixes, small features
├── medium/           # Standard features, refactoring
├── complex/          # Architecture changes, large features
├── real-world/       # Actual JIRA/GitHub issues
│   ├── jira/
│   └── github/
└── synthetic/        # Generated test cases
```

## Usage Examples

### 1. From JIRA Task
```bash
prp-bench run prompts/real-world/jira/AUTH-123.prp.yaml
```

### 2. From GitHub Issue
```bash
prp-bench run prompts/real-world/github/issue-456.prp.md
```

### 3. Batch Execution
```bash
prp-bench run prompts/simple/*.prp.yaml --parallel
```

### 4. With Specific Tools
```bash
prp-bench run prompts/complex/refactor.prp.yaml --tools claude,gemini
```

## Prompt Guidelines

### Good Prompts Include:
- Clear, specific goals
- Technical requirements
- Validation criteria
- Expected outcomes

### Avoid:
- Vague requirements
- Missing context
- No success criteria
- Unrealistic expectations

## Telemetry Integration

Each prompt execution captures:
- Start/end timestamps
- Token usage (input/output)
- Cost estimation
- Files created/modified
- Validation results
- Error logs

## Example: Real JIRA Task

```yaml
name: "PROJ-1234: Add rate limiting to API"
description: "Implement rate limiting to prevent API abuse"
type: "feature"
complexity: "medium"
tags: ["api", "security", "performance"]

prompt: |
  As a developer, I want to implement rate limiting on our REST API
  to prevent abuse and ensure fair usage across all clients.
  
  ## Acceptance Criteria
  - Rate limit of 100 requests per minute per API key
  - Return 429 (Too Many Requests) when limit exceeded
  - Include rate limit headers in responses
  - Redis-based implementation for distributed systems
  - Bypass rate limiting for admin users
  
  ## Technical Notes
  - Use Redis for storing request counts
  - Implement as FastAPI middleware
  - Add configuration for different tiers
  
validation:
  tests:
    - "pytest tests/test_rate_limiting.py"
  integration:
    - description: "Verify rate limiting works"
      command: "python scripts/test_rate_limit.py"
      expected: "429 after 100 requests"
```

## Benchmarking Metrics

For each prompt, we collect:
- **Execution Time**: Total time from start to validation
- **Token Usage**: Input/output tokens per tool
- **Cost**: Estimated cost per tool
- **Success Rate**: Validation pass/fail
- **Code Quality**: Lines added/modified, test coverage
- **Resource Usage**: CPU, memory, disk I/O