# OSOP Workflow Examples for Semantic Kernel

[OSOP](https://github.com/osopcloud/osop-spec) (Open Standard for Orchestration Protocols) is a portable YAML format for describing AI workflows — think OpenAPI, but for agent orchestration.

## What's Here

| File | Description |
|------|-------------|
| `code-review-pipeline.osop.yaml` | Automated PR review: fetch diff, parallel analysis (complexity + security + tests), generate review, post comments |

## Why OSOP?

Semantic Kernel provides powerful AI orchestration with plugins, planners, and agents. OSOP provides a **framework-agnostic way to describe** those orchestration patterns so they can be:

- **Documented** — readable YAML that non-developers can understand
- **Validated** — check workflow structure before execution
- **Ported** — same workflow definition works across Semantic Kernel, LangChain, AutoGen, etc.
- **Visualized** — render the workflow as a graph in the [OSOP Editor](https://github.com/osopcloud/osop-editor)

## Quick Start

```bash
# Validate the workflow
pip install osop
osop validate code-review-pipeline.osop.yaml

# Or just read the YAML — it's self-documenting
cat code-review-pipeline.osop.yaml
```

## How It Maps to Semantic Kernel

| OSOP Concept | Semantic Kernel Equivalent |
|---|---|
| `node` with `type: agent` | `ChatCompletionAgent` / `OpenAIAssistantAgent` |
| `node` with `type: api` | Native function / Plugin |
| `edge` with `mode: parallel` | Parallel plugin execution |
| `edge` with `mode: conditional` | `KernelFunction` with conditional logic |
| `config.plugins` | Semantic Kernel plugins |

## Learn More

- [OSOP Spec](https://github.com/osopcloud/osop-spec) — full specification
- [OSOP Examples](https://github.com/osopcloud/osop-examples) — 30+ workflow templates
- [OSOP Editor](https://github.com/osopcloud/osop-editor) — visual workflow editor
