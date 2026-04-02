# OSOP Workflow Examples for Semantic Kernel

[OSOP](https://github.com/Archie0125/osop-spec) (Open Standard Operating Procedures) is a portable YAML format for describing AI workflows — think OpenAPI, but for agent orchestration.

> **Note:** The OSOP YAML file is a declarative workflow description. The Python script `osop_workflow_reader.py` demonstrates how to read it and create Semantic Kernel agents from the definition.

## What's Here

| File | Description |
|------|-------------|
| `code-review-pipeline.osop.yaml` | OSOP workflow definition: automated PR review pipeline |
| `osop_workflow_reader.py` | Python script that reads the OSOP file and creates SK `ChatCompletionAgent` instances |

## How to Run

```bash
# Install dependencies
pip install pyyaml semantic-kernel

# Run the sample
cd python/samples/concepts/osop
python osop_workflow_reader.py
```

The script:
1. Loads the `.osop.yaml` workflow definition
2. Prints a human-readable workflow summary
3. Creates `ChatCompletionAgent` instances for each `type: agent` node
4. Invokes the first agent as a demonstration

## How It Maps to Semantic Kernel

| OSOP Concept | Semantic Kernel Equivalent |
|---|---|
| `node` with `type: agent` | `ChatCompletionAgent` |
| `node` with `type: api` | Native function / Plugin |
| `edge` with `mode: parallel` | Parallel plugin execution |
| `edge` with `mode: conditional` | `KernelFunction` with conditional logic |
| `config.plugins` | Semantic Kernel plugins |

## Learn More

- [OSOP Spec](https://github.com/Archie0125/osop-spec) — full specification (Apache 2.0)
- [OSOP Examples](https://github.com/Archie0125/osop-examples) — 84+ workflow templates
- [OSOP Visual Editor](https://osop-editor.vercel.app) — visual workflow editor
