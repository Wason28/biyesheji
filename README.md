# embodied-agent-prototype

Desktop embodied intelligence prototype for a perception-decision-execution robotic sorting workflow.

## Status

This repository has completed the phase-1 skeleton and now provides a minimal runnable mock closed-loop integration entry.

## Run

- Install dependencies: `uv pip install -e . pytest`
- Minimal validation: `uv run pytest -q`
- Unified startup entry: `uv run python -m embodied_agent.app --instruction "抓取桌面方块"`
- Dump final state: `uv run python -m embodied_agent.app --instruction "抓取桌面方块" --dump-final-state`
- Perception tool listing: `uv run python -m embodied_agent.perception.server --list-tools`

Current runtime remains mock-first: the unified entry assembles config loading, mock MCP-style services, and decision execution for local integration validation.

## Structure

- `docs/`: project specifications and progress records
- `src/embodied_agent/`: Python package for decision, perception, and execution layers
- `config/`: example runtime configuration
- `tests/`: minimal smoke and contract tests
