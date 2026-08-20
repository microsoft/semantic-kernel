# TypeScript Semantic Kernel SDK

This directory contains the TypeScript implementation of the Semantic Kernel SDK with comprehensive examples and a robust build pipeline.

## Quick Start

```bash
# Install dependencies
npm install

# Run a simple example
OPENAI_API_KEY=your_key npm run examples:01

# Run all examples
npm run examples

# Build the project
npm run build
```

## Examples

The SDK includes comprehensive examples demonstrating various capabilities. Each example is self-contained and well-documented.

### 🚀 [01-quick-chat.ts](./examples/01-quick-chat.ts)
**Basic kernel usage** - Minimal "Hello Kernel" script showing how to create a kernel, add OpenAI chat completion, and get a response.
```bash
npm run examples:01
```

### ⏰ [02-time-plugin.ts](./examples/02-time-plugin.ts)  
**Function calling with TimePlugin** - Demonstrates registering plugins and function calling by asking "What time is it in UTC +1 hour?"
```bash
npm run examples:02
```

### 🌤️ [03-custom-weather-plugin.ts](./examples/03-custom-weather-plugin.ts)
**Custom plugin development** - Shows how to create custom plugins with auto-generated JSON schemas and function calling loops.
```bash
npm run examples:03
```

### 🧠 [04-memory-rag.ts](./examples/04-memory-rag.ts)
**Vector memory and RAG** - Demonstrates creating an in-memory vector store, upserting documents, and performing semantic search for retrieval-augmented generation.
```bash
npm run examples:04
```

### 🔗 [05-planner-multistep.ts](./examples/05-planner-multistep.ts)
**Multi-step function calling** - Advanced example showing complex multi-step planning and execution workflows.
```bash
npm run examples:05
```

### 📚 [06-rag-pipeline.ts](./examples/06-rag-pipeline.ts)
**Complete RAG pipeline** - Full implementation of a retrieval-augmented generation pipeline with document processing and context injection.
```bash
npm run examples:06
```

### 🖥️ [07-mcp-server.ts](./examples/07-mcp-server.ts)
**Model Context Protocol server** - Implementation of MCP server for structured AI model interactions.
```bash
npm run examples:07
```

### 🦕 [08-deno-compat.ts](./examples/08-deno-compat.ts)
**Deno runtime compatibility** - Shows how to use the SDK with Deno runtime.
```bash
npm run examples:08
# or with Deno: deno run --allow-env --allow-net examples/08-deno-compat.ts
```

### Running Examples

Run individual examples:
```bash
OPENAI_API_KEY=your_key npm run examples:01
OPENAI_API_KEY=your_key npm run examples:02
# ... etc
```

Run all examples at once:
```bash
OPENAI_API_KEY=your_key npm run examples
```

### Example Plugins

The examples include custom plugins in [`./examples/plugins/`](./examples/plugins/):
- **[TimePlugin](./examples/plugins/TimePlugin.ts)** - Provides current time functions with timezone support
- **[WeatherPlugin](./examples/plugins/WeatherPlugin.ts)** - Mock weather service with current conditions and forecasts

## Getting Started

For a step-by-step tutorial, see the [Getting Started Guide](./GETTINGSTARTED.md). For installation details, check the [Installation Guide](./INSTALL.md).

## Features

- **Dual Package Support**: Generates both CommonJS (`.cjs`) and ESM (`.mjs`) bundles
- **Type Declarations**: Full TypeScript type definitions with source maps
- **Source Maps**: Debugging support for both formats
- **Linting**: ESLint with TypeScript support
- **Testing**: Jest with coverage reporting
- **Documentation**: TypeDoc for API documentation generation
- **CI/CD**: GitHub Actions pipeline

## Development

### Basic Workflow
```bash
# Install dependencies
npm install

# Development workflow
npm run clean
npm run build
npm test

# Generate documentation
npm run docs

# Lint and fix code
npm run lint:fix
```

### Build Scripts

| Command | Description |
|---------|-------------|
| `npm run build` | Full build pipeline (clean → type-check → esbuild → types) |
| `npm run build:esbuild` | Generate CommonJS and ESM bundles with source maps |
| `npm run build:types` | Generate TypeScript declarations |
| `npm run clean` | Remove all build artifacts |
| `npm run type-check` | Type checking without emitting files |
| `npm run lint` | ESLint code analysis |
| `npm run lint:fix` | Auto-fix linting issues |
| `npm run test` | Run tests |
| `npm run test:watch` | Run tests in watch mode |
| `npm run test:coverage` | Run tests with coverage report |
| `npm run docs` | Generate API documentation |
| `npm run dev` | Build and run the generated bundle |

## External Dependencies

The bundles externalize these dependencies (must be installed separately):
- `openai` - OpenAI SDK  
- `zod` - Schema validation
- `@opentelemetry/api` - Observability

This keeps the bundle size minimal while supporting tree-shaking in consuming applications.

## Build Pipeline Details

### Output Structure

```
dist/
├── index.cjs           # CommonJS bundle
├── index.cjs.map       # CommonJS source map
├── index.mjs           # ESM bundle  
├── index.mjs.map       # ESM source map
├── index.d.ts          # Main type declarations
├── *.d.ts              # Individual module declarations
├── *.d.ts.map          # Declaration source maps
└── package.json        # Dual package exports configuration
```

### Package Exports

The generated `dist/package.json` supports dual package exports:

```json
{
  "main": "./index.cjs",
  "module": "./index.mjs", 
  "types": "./index.d.ts",
  "exports": {
    ".": {
      "import": "./index.mjs",
      "require": "./index.cjs",
      "types": "./index.d.ts"
    }
  }
}
```

### CI Pipeline

The GitHub Actions workflow (`.github/workflows/typescript.yml`) runs:

1. **Lint** - Code quality checks
2. **Type Check** - TypeScript compilation validation
3. **Build** - Generate dual bundles and type declarations
4. **Test** - Run test suite with coverage
5. **Docs** - Generate API documentation

The pipeline runs on Node.js 18.x and 20.x for compatibility testing.