# Getting Started with TypeScript Semantic Kernel

This 5-minute tutorial will get you up and running with the TypeScript Semantic Kernel SDK.

## Quick Setup

First, make sure you have the prerequisites from the [Installation Guide](./INSTALL.md):

```bash
# Check Node.js version (requires 18+)
node --version

# Set your OpenAI API key
export OPENAI_API_KEY="your_openai_api_key_here"
```

## Hello Semantic Kernel

Let's start with the simplest possible example - a basic chat interaction:

```typescript
import { Kernel, OpenAIChatCompletion } from 'semantic-kernel';

async function quickChat() {
  // 1. Create a kernel instance
  const kernel = new Kernel();
  
  // 2. Add OpenAI chat completion service
  const openai = new OpenAIChatCompletion({
    apiKey: process.env.OPENAI_API_KEY,
    model: 'gpt-4o'
  });
  kernel.addService(openai, 'chat');
  
  // 3. Send a prompt and get a response
  const response = await kernel.chat('Hello! Tell me a fun fact about TypeScript.');
  console.log('🤖 Assistant:', response.content);
}

quickChat();
```

Save this as `hello-kernel.ts` and run:

```bash
npx tsx hello-kernel.ts
```

**Expected Output:**
```
🤖 Assistant: TypeScript was created by Microsoft and was first released in 2012. One fun fact is that TypeScript code is transpiled to JavaScript, which means you can gradually adopt it in existing JavaScript projects without having to rewrite everything from scratch!
```

## Adding Plugins with Function Calling

Now let's extend our example with a TimePlugin to demonstrate function calling:

```typescript
import { Kernel, OpenAIChatCompletion } from 'semantic-kernel';
import { Context } from 'semantic-kernel';

// Simple time plugin
class TimePlugin {
  async getCurrentTimeUtc(context: Context): Promise<string> {
    return new Date().toISOString();
  }
  
  async getCurrentTimeWithOffset(context: Context): Promise<string> {
    const { offsetHours } = context.variables;
    const now = new Date();
    const utcTime = now.getTime() + (now.getTimezoneOffset() * 60000);
    const targetTime = new Date(utcTime + (offsetHours * 3600000));
    return targetTime.toISOString();
  }
}

async function timeExample() {
  // Create kernel and add OpenAI service
  const kernel = new Kernel();
  const openai = new OpenAIChatCompletion({
    apiKey: process.env.OPENAI_API_KEY
  });
  kernel.addService(openai, 'chat');
  
  // Register the TimePlugin
  const timePlugin = new TimePlugin();
  kernel.addPlugin(timePlugin, 'time');
  
  // Ask a question that requires function calling
  const response = await kernel.chat('What time is it in UTC +1 hour?');
  console.log('🤖 Assistant:', response.content);
}

timeExample();
```

The kernel will automatically:
1. Detect that the question requires time information
2. Call the appropriate plugin function
3. Use the function result to generate a helpful response

## Memory and Retrieval-Augmented Generation (RAG)

Let's add memory capabilities for context-aware responses:

```typescript
import { Kernel, OpenAIChatCompletion, InMemoryVectorStore } from 'semantic-kernel';

async function ragExample() {
  const kernel = new Kernel();
  
  // Add services
  const openai = new OpenAIChatCompletion({ apiKey: process.env.OPENAI_API_KEY });
  kernel.addService(openai, 'chat');
  
  const memoryStore = new InMemoryVectorStore();
  kernel.registerMemoryStore(memoryStore);
  
  // Create knowledge base
  await memoryStore.createCollection('docs');
  
  // Add some documents (with simple embeddings for demo)
  const docs = [
    'TypeScript is a strongly typed programming language.',
    'Semantic Kernel enables AI orchestration and function calling.',
    'Vector databases allow semantic search over documents.'
  ];
  
  for (let i = 0; i < docs.length; i++) {
    await memoryStore.upsert('docs', {
      id: `doc-${i}`,
      embedding: mockEmbedding(docs[i]), // Simple embedding function
      metadata: { text: docs[i] }
    });
  }
  
  // Query with context
  const query = 'Tell me about TypeScript';
  const queryEmbedding = mockEmbedding(query);
  const results = await memoryStore.getNearestMatches('docs', queryEmbedding, 2);
  
  const context = results.map(r => r.metadata?.text).join('\n');
  const promptWithContext = `Context:\n${context}\n\nQuestion: ${query}`;
  
  const response = await kernel.chat(promptWithContext);
  console.log('🤖 Assistant:', response.content);
}

// Simple embedding function for demo
function mockEmbedding(text: string): number[] {
  return text.split('').slice(0, 10).map(char => char.charCodeAt(0) / 255);
}

ragExample();
```

## Console Output Examples

Here's what you should see when running the examples:

### Quick Chat Example
```
🤖 Assistant: TypeScript was created by Microsoft and was first released in 2012...
```

### Time Plugin Example
```
🕒 Asking about time in UTC+1...
🤖 Assistant: The current time in UTC+1 is 2024-01-15T15:30:45.123Z. This is Central European Time (CET).
```

### RAG Example
```
📚 Setting up vector memory with sample documents...
🔍 Searching for similar documents...
Found 2 similar documents:
  1. TypeScript is a strongly typed programming language.
  2. Semantic Kernel enables AI orchestration and function calling.
🤖 Generating response with retrieved context...
🤖 Assistant: Based on the context, TypeScript is a strongly typed programming language...
```

## Explore More Examples

The repository includes comprehensive examples:

- `01-quick-chat.ts` - Basic kernel usage
- `02-time-plugin.ts` - Function calling with TimePlugin
- `03-custom-weather-plugin.ts` - Custom plugin development
- `04-memory-rag.ts` - Vector memory and RAG
- `05-planner-multistep.ts` - Multi-step function calling
- `06-rag-pipeline.ts` - Complete RAG pipeline
- `07-mcp-server.ts` - Model Context Protocol server
- `08-deno-compat.ts` - Deno runtime compatibility

Run all examples:
```bash
cd typescript && npm run examples
```

## Next Steps

- **Conceptual Learning**: Visit the [official Semantic Kernel documentation](https://learn.microsoft.com/en-us/semantic-kernel/)
- **Advanced Examples**: Explore the [examples directory](./examples/)
- **API Reference**: Check the generated [TypeDoc documentation](./docs/)
- **Build Details**: Read the [TypeScript README](./README.md) for development setup

## Getting Help

- Check existing [examples](./examples/) for common patterns
- Review the [installation guide](./INSTALL.md) for setup issues
- Open GitHub issues for bugs or feature requests
- Consult the [Microsoft Learn Quick-Start Guide](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide) for deeper conceptual understanding

Happy coding with TypeScript Semantic Kernel! 🚀