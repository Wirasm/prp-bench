# PRP-Bench Architecture

## Overview

PRP-Bench (Prompt Response Performance Benchmark) is a benchmarking tool for comparing AI coding CLI tools (Claude Code, Gemini CLI, opencode (STT), and Codex CLI) by executing the same prompts across all tools and collecting performance metrics.

## Vertical Architecture

```
src/prp_bench/
├── __init__.py
├── main.py                    # Entry point
├── config.py                  # Configuration management
├── models.py                  # Pydantic data models
├── tests/
│   ├── test_main.py
│   ├── test_config.py
│   └── test_models.py
│
├── cli/                       # CLI tool abstractions
│   ├── __init__.py
│   ├── base.py               # Abstract base runner
│   ├── claude_code.py        # Claude Code runner
│   ├── gemini.py             # Gemini CLI runner
│   ├── codex.py              # Codex CLI runner
│   └── tests/
│       ├── test_base.py
│       ├── test_claude_code.py
│       ├── test_gemini.py
│       └── test_codex.py
│
├── prompts/                   # Prompt management
│   ├── __init__.py
│   ├── loader.py             # Prompt file loading
│   ├── parser.py             # Prompt parsing
│   └── tests/
│       ├── test_loader.py
│       └── test_parser.py
│
├── telemetry/                 # Telemetry collection
│   ├── __init__.py
│   ├── collector.py          # Base telemetry collector
│   ├── claude_collector.py   # Claude OTel collector
│   ├── gemini_collector.py   # Gemini stats collector
│   ├── codex_collector.py    # Codex metrics collector
│   ├── aggregator.py         # Metrics aggregation
│   └── tests/
│       ├── test_collector.py
│       ├── test_claude_collector.py
│       └── test_aggregator.py
│
├── execution/                 # Execution orchestration
│   ├── __init__.py
│   ├── runner.py             # Main execution runner
│   ├── scheduler.py          # Parallel/sequential scheduling
│   ├── sandbox.py            # Sandboxed execution environment
│   └── tests/
│       ├── test_runner.py
│       ├── test_scheduler.py
│       └── test_sandbox.py
│
├── reporting/                 # Results reporting
│   ├── __init__.py
│   ├── formatter.py          # Output formatting
│   ├── exporter.py           # Export to various formats
│   ├── visualizer.py         # Charts and graphs
│   └── tests/
│       ├── test_formatter.py
│       └── test_exporter.py
│
└── utils/                     # Utilities
    ├── __init__.py
    ├── process.py            # Process management
    ├── filesystem.py         # File operations
    ├── timer.py              # Timing utilities
    └── tests/
        ├── test_process.py
        └── test_timer.py
```

## Core Components

### 1. CLI Runners (`cli/`)

Abstract base class with implementations for each tool:

- Handle authentication setup
- Execute prompts in headless mode
- Capture output and errors
- Manage process lifecycle

### 2. Telemetry Collection (`telemetry/`)

- Claude: OpenTelemetry integration
- Gemini: Stats command parsing
- Codex: Basic metrics collection
- Unified aggregation layer

### 3. Prompt Management (`prompts/`)

- Support multiple prompt formats (text, markdown, YAML)
- Metadata extraction (expected outcomes, tags)
- Prompt validation and preprocessing

### 4. Execution Engine (`execution/`)

- Orchestrate parallel/sequential runs
- Sandbox management for isolation
- Resource monitoring
- Timeout handling

### 5. Reporting (`reporting/`)

- Real-time progress display
- Final results aggregation
- Export to JSON, CSV, HTML
- Visualization of metrics

## Data Flow

1. **Input**: Prompt file(s) → Parser → Validation
2. **Execution**: Scheduler → CLI Runners → Sandboxed processes
3. **Collection**: Process output → Telemetry collectors → Aggregator
4. **Output**: Formatter → Reports/Visualizations

## Key Design Decisions

### Vertical Slicing

Each feature is self-contained with its own tests, following the CLAUDE.md guidelines.

### Dependency Injection

CLI runners and collectors are injected, allowing easy extension for new tools.

### Sandboxing

Each tool runs in an isolated environment to prevent interference.

### Telemetry Abstraction

Unified interface for different telemetry systems (OTel, custom stats, etc.)

### Configuration Management

Hierarchical configuration (CLI args > env vars > config file > defaults).

## Security Considerations

- API keys managed via environment variables
- Sandboxed execution prevents file system damage
- Timeout limits prevent infinite loops
- Resource limits prevent memory/CPU exhaustion

## Extensibility

- Add new CLI tools by implementing base runner
- Add new telemetry sources by implementing collector
- Add new output formats by implementing exporter
- Plugin system for custom metrics
