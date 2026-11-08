# Contributing to Universal API Assurance (UAA)

We welcome contributions to UAA! Whether you are adding a new framework discovery adapter, protocol runner, security check rule, or agent skill, please follow these guidelines.

## Architectural Boundaries

Remember that UAA is strictly divided into two layers:
1. **Agent Skills Layer (`skills/`)**:
   - Contains agent prompts, checklists, and reference guides.
   - Designed for LLM coding assistants.
2. **Assurance Engine Layer (`engine/`, `adapters/`, `validators/`, `schemas/`)**:
   - Zero external third-party dependencies (Python 3.9+ standard library only).
   - Deterministic and testable via `python -m unittest discover tests`.
   - Never place framework-specific assumptions into core `engine/`.

## Development & Testing Workflow

1. **Run All Tests**:
   ```bash
   python -m unittest discover tests
   ```
2. **Validate Schemas**:
   ```bash
   python -m engine.cli validate inventory --file examples/basic-rest/endpoint-inventory.json
   python -m engine.cli validate testspec --file examples/basic-rest/testspecifications.json
   python -m engine.cli validate ledger --file examples/basic-rest/coverage-ledger.json
   ```
3. **Adding Adapters**:
   - Discovery adapters: implement in `adapters/discovery/<framework>/` and add unit test in `tests/compatibility/`.
   - Protocol runners: implement in `adapters/protocols/<protocol>/`.
4. **Code Style**:
   - Python 3.9+ typing.
   - Preserve comments and docstrings.

