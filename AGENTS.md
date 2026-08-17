# AGENTS.md

## Start here

Before changing code or documentation:

1. Read `CONTRIBUTING.md`.
2. Confirm which part of the repository owns the behavior you are changing.
3. Search for existing implementations and tests before adding new abstractions.
4. Keep the change focused on the relevant issue.

Use this file as navigation guidance for AI coding assistants; `CONTRIBUTING.md` remains the source of truth for contribution and PR requirements.

## Repository map

### .NET

The main .NET source is under `dotnet/`.

Use these areas as starting points:

- `dotnet/src/SemanticKernel.Abstractions` — public abstractions and contracts.
- `dotnet/src/SemanticKernel.Core` — core Semantic Kernel functionality.
- `dotnet/src/Agents` — agent implementations and related components.
- `dotnet/src/Connectors` — service and provider connectors.
- `dotnet/src/Plugins` — plugins and plugin-related components.
- `dotnet/src/VectorData` — vector-data integrations and related memory components.
- `dotnet/src/SemanticKernel.UnitTests` — unit tests for core functionality.
- `dotnet/src/IntegrationTests` — integration tests.
- `dotnet/src/Plugins/Plugins.UnitTests` — plugin and memory-related unit tests.

For planner/kernel work, search the existing implementation and neighboring tests first rather than assuming a single entry point. In the current .NET tree, planning-related code is under `dotnet/src/InternalUtilities/planning`.

### Python

The Python source is under `python/`.

Useful starting points:

- `python/semantic_kernel` — package source.
- `python/tests/unit` — unit tests.
- `python/tests/integration` — integration tests.
- `python/samples` — examples.
- `python/DEV_SETUP.md` — environment, testing, and quality-check instructions.

### Java

Java implementation work belongs in the separate
[`microsoft/semantic-kernel-java`](https://github.com/microsoft/semantic-kernel-java) repository.

The `java/README.md` redirects Java development to that repository; do not add Java implementation changes here.

## Build, test, and quality checks

### .NET

From `dotnet/`:

```text
build.cmd
```

The repository's `build.cmd` performs a Release build followed by the Release test suite.

For formatting:

```text
dotnet format
```

When possible, run the smallest relevant test project first, then broader validation.

### Python

Follow `python/DEV_SETUP.md` for environment setup.

Unit tests:

```text
uv run pytest tests/unit
```

Integration tests:

```text
uv run pytest tests/integration
```

All tests:

```text
uv run pytest tests
```

From `python/`:

```text
uv run pre-commit run -a
```

## Connectors, plugins, memory, and vector data

Before adding or changing a connector, plugin, memory implementation, or vector-data component:

1. Find a nearby implementation with similar behavior.
2. Reuse the existing abstraction and configuration pattern.
3. Read the corresponding tests before changing production code.
4. Confirm that the contribution belongs in this repository.

`CONTRIBUTING.md` explicitly recommends hosting plugins and memory connectors outside this repository rather than adding them in-tree.

## APIs and compatibility

Preserve existing API signatures and behavioral compatibility.

Do not introduce a new public API or a breaking change without the required issue and maintainer discussion described in `CONTRIBUTING.md`.

When a concept exists across languages, check the existing implementation and documentation for each relevant language. Do not assume that C#, Python, and Java share the same repository layout or identical APIs.

## Security and secrets

Never commit credentials or sensitive local configuration, including:

- API keys
- access tokens
- passwords
- private certificates
- secret-bearing `.env` files

For Python development, `DEV_SETUP.md` also instructs contributors not to store `*.env` files in the repository.

For security-sensitive changes, read `SECURITY.md` and inspect relevant tests before changing behavior.

## Tests and change validation

For behavior changes:

1. Identify the closest existing tests.
2. Add a focused regression or feature test when applicable.
3. Prefer deterministic tests over tests that depend on external services.
4. Run the relevant formatter and test suite.
5. Review the final diff before opening the PR.

Before opening a PR, at minimum review:

```text
git status
git diff --check
git diff
```

Confirm that the diff is focused, contains no unrelated files or secrets, and that documentation matches the current repository structure.

Follow `CONTRIBUTING.md` for the complete PR workflow.
