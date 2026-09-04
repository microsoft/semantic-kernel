# Python Connector Extras and Optional Dependencies

This page maps every public Python connector under `semantic_kernel/connectors/` to the
install extra it needs and to the upstream package(s) and version constraints that extra
declares in [`pyproject.toml`](../pyproject.toml).

Connectors that need no extra say `none` explicitly — they only rely on packages that are
already part of the base `semantic-kernel` install.

## How to install

```bash
# from PyPI
pip install semantic-kernel[<extra>]
pip install semantic-kernel[azure,redis]        # more than one extra

# from a clone of this repository
uv sync --extra <extra>
uv sync --all-extras --dev                      # everything, what CI installs
```

Extra names are the keys of `[project.optional-dependencies]` in
[`pyproject.toml`](../pyproject.toml). Installing an extra never changes the base install:
these packages are optional on purpose, and adding a connector to the default install or
widening a constraint is out of scope for this page.

## AI service connectors

Import path is the public module; see [AI connectors README](../semantic_kernel/connectors/ai/README.md)
for the concrete service classes each one exports.

| Connector | Import path | Install extra | Upstream package(s) & constraint |
| --- | --- | --- | --- |
| Anthropic | `semantic_kernel.connectors.ai.anthropic` | `anthropic` | `anthropic ~= 0.32` |
| Azure AI Inference | `semantic_kernel.connectors.ai.azure_ai_inference` | `azure` | `azure-ai-inference >= 1.0.0b6`, `azure-core-tracing-opentelemetry >= 1.0.0b11` |
| Amazon Bedrock | `semantic_kernel.connectors.ai.bedrock` | `aws` | `boto3>=1.36.4,<1.43.0` |
| Google AI / Vertex AI | `semantic_kernel.connectors.ai.google` | `google` | `google-genai >= 1.51,< 1.75`, `google-cloud-aiplatform>=1.114,<1.134` |
| Hugging Face | `semantic_kernel.connectors.ai.hugging_face` | `hugging_face` | `transformers[torch] >= 4.28,< 6.0`, `sentence-transformers >= 2.2,< 6.0`, `torch==2.13.0` |
| Mistral AI | `semantic_kernel.connectors.ai.mistral_ai` | `mistralai` | `mistralai >= 1.2,< 2.7.3` |
| NVIDIA NIM | `semantic_kernel.connectors.ai.nvidia` | `none` | `openai >= 2.0.0` (base dependency; the connector talks to NIM through the OpenAI client) |
| Ollama | `semantic_kernel.connectors.ai.ollama` | `ollama` | `ollama ~= 0.4` |
| ONNX GenAI | `semantic_kernel.connectors.ai.onnx` | `onnx` | `onnxruntime==1.22.1`, `onnxruntime>=1.26.0`, `onnxruntime-genai==0.9.0`, `onnxruntime-genai==0.14.1` (selected by python_version marker) |
| OpenAI / Azure OpenAI | `semantic_kernel.connectors.ai.open_ai` | `none` | `openai >= 2.0.0` (base dependency) |

The realtime clients exported by `semantic_kernel.connectors.ai.open_ai`
(`OpenAIRealtimeWebsocket`, `AzureRealtimeWebRTC`, ...) need `websockets` and `aiortc`.
Both are base dependencies, so no extra is required; the `realtime` extra declares the same
two packages and exists as an explicit opt-in name rather than as an additional install.

## Vector store, search and protocol connectors

| Connector | Import path | Install extra | Upstream package(s) & constraint |
| --- | --- | --- | --- |
| Azure AI Search | `semantic_kernel.connectors.azure_ai_search` | `azure` | `azure-search-documents >= 11.6.0b4, < 13.0.0` |
| Azure Cosmos DB NoSQL | `semantic_kernel.connectors.azure_cosmos_db` | `azure` | `azure-cosmos ~= 4.7` |
| Azure Cosmos DB for MongoDB (vCore) | `semantic_kernel.connectors.azure_cosmos_db` | `azure` and `mongo` | `azure-cosmos ~= 4.7`, `pymongo >= 4.8.0, < 4.17` |
| Brave Search | `semantic_kernel.connectors.brave` | `none` | `httpx`, already installed as a transitive dependency of the base install |
| Chroma | `semantic_kernel.connectors.chroma` | `chroma` | `chromadb >= 0.5,< 1.6` |
| Faiss | `semantic_kernel.connectors.faiss` | `faiss` | `faiss-cpu>=1.10.0` |
| Google Web Search | `semantic_kernel.connectors.google_search` | `none` | `httpx`, already installed as a transitive dependency of the base install |
| In-memory store | `semantic_kernel.connectors.in_memory` | `none` | `numpy >= 1.25.0`, `numpy >= 1.26.0`, `scipy>=1.15.1` (base dependencies) |
| MCP (stdio, SSE, streamable HTTP, websocket) | `semantic_kernel.connectors.mcp` | `mcp` (optional — `mcp` is also a base dependency) | `mcp>=1.8,<2.0` |
| MongoDB Atlas | `semantic_kernel.connectors.mongodb` | `mongo` | `pymongo >= 4.8.0, < 4.17`, `motor >= 3.3.2,< 3.8.0` |
| OpenAPI plugin | `semantic_kernel.connectors.openapi_plugin` | `none` | `openapi_core >= 0.18,<0.20`, `prance >= 23.6.21,< 26.7.20` (base dependencies) |
| Oracle 23ai | `semantic_kernel.connectors.oracle` | `oracledb` | `oracledb >= 3.4.1` |
| Pinecone | `semantic_kernel.connectors.pinecone` | `pinecone` | `pinecone[asyncio, grpc] ~= 7.0`, `pinecone[asyncio, grpc] ~= 7.3` (selected by sys_platform marker) |
| Postgres / pgvector | `semantic_kernel.connectors.postgres` | `postgres` | `psycopg[binary,pool] ~= 3.2` |
| Qdrant | `semantic_kernel.connectors.qdrant` | `qdrant` | `qdrant-client ~= 1.9` |
| Redis | `semantic_kernel.connectors.redis` | `redis` | `redis[hiredis] >= 6,< 8`, `redisvl ~= 0.4`, `types-redis ~= 4.6.0.20240425` |
| SQL Server | `semantic_kernel.connectors.sql_server` | `sql` | `pyodbc >= 5.2` |
| Weaviate | `semantic_kernel.connectors.weaviate` | `weaviate` | `weaviate-client>=4.17.0,<5.0` |

## Deprecated memory-store connectors

Everything under `semantic_kernel/connectors/memory_stores/` is marked `@deprecated` and
will be removed in a future release; prefer the vector-store connectors in the table above.
They are listed here because some extras exist only for them.

| Connector | Import path | Install extra | Upstream package(s) & constraint |
| --- | --- | --- | --- |
| AstraDB (deprecated) | `semantic_kernel.connectors.memory_stores.astradb` | `none` | `aiohttp ~= 3.8` (base dependency) |
| Azure Cognitive Search (deprecated) | `semantic_kernel.connectors.memory_stores.azure_cognitive_search` | `azure` | `azure-search-documents >= 11.6.0b4, < 13.0.0` |
| Azure Cosmos DB Mongo vCore (deprecated) | `semantic_kernel.connectors.memory_stores.azure_cosmosdb` | `mongo` | `pymongo >= 4.8.0, < 4.17` |
| Azure Cosmos DB NoSQL (deprecated) | `semantic_kernel.connectors.memory_stores.azure_cosmosdb_no_sql` | `azure` | `azure-cosmos ~= 4.7` |
| Chroma (deprecated) | `semantic_kernel.connectors.memory_stores.chroma` | `chroma` | `chromadb >= 0.5,< 1.6` |
| Milvus (deprecated) | `semantic_kernel.connectors.memory_stores.milvus` | `milvus` | `pymilvus >= 2.3,< 2.7`, `milvus >= 2.3,<2.3.8` (not installed on Windows) |
| MongoDB Atlas (deprecated) | `semantic_kernel.connectors.memory_stores.mongodb_atlas` | `mongo` | `pymongo >= 4.8.0, < 4.17` |
| Pinecone (deprecated) | `semantic_kernel.connectors.memory_stores.pinecone` | `pinecone` | `pinecone[asyncio, grpc] ~= 7.0`, `pinecone[asyncio, grpc] ~= 7.3` |
| Postgres (deprecated) | `semantic_kernel.connectors.memory_stores.postgres` | `postgres` | `psycopg[binary,pool] ~= 3.2` |
| Qdrant (deprecated) | `semantic_kernel.connectors.memory_stores.qdrant` | `qdrant` | `qdrant-client ~= 1.9` |
| Redis (deprecated) | `semantic_kernel.connectors.memory_stores.redis` | `redis` | `redis[hiredis] >= 6,< 8` |
| USearch (deprecated) | `semantic_kernel.connectors.memory_stores.usearch` | `usearch` | `usearch >= 2.16,< 2.25`, `pyarrow>=12.0,<24.0` |
| Weaviate (deprecated) | `semantic_kernel.connectors.memory_stores.weaviate` | `weaviate` | `weaviate-client>=4.17.0,<5.0` |

## Extras that are not connectors

These extras exist in `pyproject.toml` but do not belong to a connector, so they have no row
above: `autogen` and `copilotstudio` (agent integrations under `semantic_kernel/agents/`),
`notebooks` and `pandas` (sample/tooling helpers), and `realtime` (see the note under the AI
service table).

## Connector-specific configuration docs

- [All settings — constructor arguments, environment variables and settings classes per connector](../samples/concepts/setup/ALL_SETTINGS.md)
- [AI connectors overview](../semantic_kernel/connectors/ai/README.md)
- [Amazon Bedrock connector](../semantic_kernel/connectors/ai/bedrock/README.md)
- [Google AI / Vertex AI connector](../semantic_kernel/connectors/ai/google/README.md)
- [NVIDIA NIM connector](../semantic_kernel/connectors/ai/nvidia/README.md)
- [MongoDB Atlas memory store](../semantic_kernel/connectors/memory_stores/mongodb_atlas/README.md)
- [Redis memory store](../semantic_kernel/connectors/memory_stores/redis/README.md)
- [Weaviate memory store](../semantic_kernel/connectors/memory_stores/weaviate/README.md)
- [Dev setup — installing extras from a clone](../DEV_SETUP.md)

## How version constraints are validated in CI

Constraints live in exactly one place, `python/pyproject.toml`. `python/uv.lock` holds the
resolved versions for the three platforms declared in `[tool.uv] environments`
(`darwin`, `linux`, `win32`). The workflows below are what actually exercise them:

| Workflow | Install step | What it proves |
| --- | --- | --- |
| `.github/workflows/python-unit-tests.yml` | `uv sync --all-extras --dev -U --prerelease=if-necessary-or-explicit` | Every extra resolves together, on Python 3.10 / 3.11 / 3.12 across ubuntu, windows and macos (plus an experimental 3.13 ubuntu job). `-U` re-resolves to the newest versions the constraints allow, so a constraint that no longer resolves fails the PR. Tests then run with `uv run --frozen pytest ./tests/unit`. |
| `.github/workflows/python-test-coverage.yml` | `uv sync --all-extras --dev -U --prerelease=if-necessary-or-explicit` | Same all-extras resolution on Python 3.10, then the unit suite with coverage. |
| `.github/workflows/python-lint.yml` | `uv sync --all-extras --dev` | Installs from the committed `uv.lock` (re-resolving only when `pyproject.toml` changed) on Python 3.10, then runs pre-commit and `uv run mypy -p semantic_kernel` against the installed optional packages. |
| `.github/workflows/python-integration-tests.yml` | `uv sync --all-extras --dev` | The integration jobs install every extra from the committed `uv.lock` before talking to the real services. |

`astral-sh/setup-uv` is cached on `cache-dependency-glob: "**/uv.lock"` in each of those
workflows, so a lock change invalidates the cache and forces a fresh install.

Two limits worth stating plainly:

- CI installs **all** extras together. It does not install a single extra on its own, so
  "extra `X` alone is enough to import connector `X`" is not verified by CI today. The one
  exception is the dapr job in `python-unit-tests.yml`, which installs only `--extra pandas`.
- This page itself is kept in sync by
  [`tests/unit/test_connector_extras_doc.py`](../tests/unit/test_connector_extras_doc.py),
  which runs in the unit-test and coverage workflows above. It parses the tables here and
  `pyproject.toml` and fails when an extra is renamed, added or removed, or when the upstream
  package names or version constraints listed here stop matching `pyproject.toml`. Version
  specifiers in a `none` row are checked against the base `[project] dependencies`; a package
  named without a version specifier (such as `httpx` above) is documentation only and is not
  machine-checked.
