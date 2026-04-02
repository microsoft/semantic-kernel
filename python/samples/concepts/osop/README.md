# OSOP Workflow Examples for Semantic Kernel

[OSOP](https://github.com/Archie0125/osop-spec) (Open Standard Operating Procedures) is a portable YAML format for describing AI workflows — think OpenAPI, but for agent orchestration.

> **Note:** OSOP files are declarative workflow descriptions, not executable code. They document orchestration patterns in a framework-agnostic format.

## What's Here

| File | Description |
|------|-------------|
| `code-review-pipeline.osop.yaml` | Automated PR review: fetch diff, parallel analysis (complexity + security + tests), generate review, post comments |

## Why OSOP?

Semantic Kernel provides powerful AI orchestration with plugins, planners, and agents. OSOP provides a **framework-agnostic way to describe** those orchestration patterns so they can be:

- **Documented** — readable YAML that non-developers can understand
- **Validated** — check workflow structure before execution
- **Ported** — same workflow definition works across Semantic Kernel, LangChain, AutoGen, etc.
- **Visualized** — render the workflow as a graph in the [OSOP Editor](https://osop-editor.vercel.app)

## How It Maps to Semantic Kernel

| OSOP Concept | Semantic Kernel Equivalent |
|---|---|
| `node` with `type: agent` | `ChatCompletionAgent` / `OpenAIAssistantAgent` |
| `node` with `type: api` | Native function / Plugin |
| `edge` with `mode: parallel` | Parallel plugin execution |
| `edge` with `mode: conditional` | `KernelFunction` with conditional logic |
| `config.plugins` | Semantic Kernel plugins |

## Learn More

- [OSOP Spec](https://github.com/Archie0125/osop-spec) — full specification
- [OSOP Examples](https://github.com/Archie0125/osop-examples) — 84+ workflow templates
- [OSOP Visual Editor](https://osop-editor.vercel.app) — visual workflow editor
- [OSOP Website](https://osop.ai) — documentation and guides
