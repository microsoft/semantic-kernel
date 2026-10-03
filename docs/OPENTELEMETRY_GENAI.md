# OpenTelemetry GenAI instrumentation sample

The community project [otel-genai-bridges](https://github.com/dineshkumarkummara/otel-genai-bridges) includes a .NET library (`SkOtel`) and sample (`dotnet/samples/sk-chat`) that instrument Semantic Kernel applications using the [OpenTelemetry Generative AI semantic conventions](https://github.com/open-telemetry/semantic-conventions/tree/main/docs/gen-ai).

## Highlights

- `AddSemanticKernelTelemetry` extension registers telemetry options, middleware, and a DelegatingHandler.
- Middleware captures prompts, completions, tool invocations, latency, token usage, cost, and RAG retrieval latency.
- Docker Compose stack (OpenTelemetry Collector → Tempo/Prometheus → Grafana) and dashboards are provided out of the box.

## Quick start

```bash
# Clone the repository
git clone https://github.com/dineshkumarkummara/otel-genai-bridges.git
cd otel-genai-bridges

# Launch the collector, Tempo, Prometheus, Grafana, and both sample apps
./scripts/run_all.sh
```

The Semantic Kernel sample listens on `http://localhost:7080`. Send prompts to `/chat` or `/rag` with `curl` to generate telemetry.

![Grafana token throughput panel](https://github.com/dineshkumarkummara/otel-genai-bridges/raw/main/docs/screenshots/grafana-tokens.png)

The Grafana dashboard (http://localhost:3000/d/genai-overview) surfaces latency, token usage, error rates, tool-call counts, and RAG retrieval latency. Tempo provides trace waterfalls showing prompt/response events and tool execution spans.

For more details or to contribute, visit the repository: https://github.com/dineshkumarkummara/otel-genai-bridges.
