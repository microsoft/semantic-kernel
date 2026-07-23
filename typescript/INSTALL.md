# Installation Guide

This guide will help you install and set up the TypeScript Semantic Kernel SDK.

## Prerequisites

- **Node.js 18+** - Download from [nodejs.org](https://nodejs.org/)
- **Package Manager** - npm (comes with Node.js) or pnpm (recommended)
- **Git** - For cloning the repository
- **TypeScript Knowledge** - Basic familiarity with TypeScript

## Environment Variables

Before using the SDK, you'll need to set up your API keys:

### Required

- `OPENAI_API_KEY` - Your OpenAI API key from [platform.openai.com](https://platform.openai.com/)

### Optional

- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI service endpoint
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT_NAME` - Azure OpenAI deployment name
- `OPENAI_MODEL` - OpenAI model to use (default: `gpt-4o`)

Set these in your shell or create a `.env` file:

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

## Installation Options

### Option 1: NPM Package (Recommended)

```bash
npm install semantic-kernel
```

### Option 2: Local Development

Clone and build from source:

```bash
# Clone the repository
git clone https://github.com/atveit/codextesting.git
cd codextesting/typescript

# Install dependencies
npm install

# Build the project
npm run build

# Link for local development
npm link
```

In your project:

```bash
npm link semantic-kernel
```

## Running Examples

After installation, you can run the included examples:

### Using NPM Package

```bash
# Quick chat example
OPENAI_API_KEY=your_key npx tsx examples/01-quick-chat.ts

# Time plugin example
OPENAI_API_KEY=your_key npx tsx examples/02-time-plugin.ts

# Weather plugin example
OPENAI_API_KEY=your_key npx tsx examples/03-custom-weather-plugin.ts
```

### Using Local Build

```bash
# Install tsx for TypeScript execution
npm install -g tsx

# Run examples
cd typescript
npm run examples:01
npm run examples:02
npm run examples:03
```

### All Examples at Once

```bash
npm run examples
```

## Deno Support

The SDK also works with Deno:

```bash
# Install Deno
curl -fsSL https://deno.land/install.sh | sh

# Run Deno example
OPENAI_API_KEY=your_key deno run --allow-env --allow-net examples/08-deno-compat.ts
```

## Verification

Test your installation with a simple script:

```typescript
import { Kernel, OpenAIChatCompletion } from 'semantic-kernel';

const kernel = new Kernel();
const openai = new OpenAIChatCompletion({
  apiKey: process.env.OPENAI_API_KEY
});
kernel.addService(openai, 'chat');

const response = await kernel.chat('Hello, world!');
console.log(response.content);
```

Save as `test.ts` and run:

```bash
OPENAI_API_KEY=your_key npx tsx test.ts
```

## Troubleshooting

### Common Issues

1. **"Connection error"** - Check your `OPENAI_API_KEY` is valid
2. **"Unknown file extension .ts"** - Install `tsx`: `npm install -g tsx`
3. **"Module not found"** - Run `npm install` in the project directory
4. **Deno permissions** - Use `--allow-env --allow-net` flags

### Support

- Check the [examples directory](./examples/) for working code
- Review the [Getting Started Guide](./GETTINGSTARTED.md)
- Open an issue on GitHub for bugs

## Next Steps

- Read the [Getting Started Guide](./GETTINGSTARTED.md)
- Explore the [examples](./examples/)
- Check out the [TypeScript README](./README.md) for build details