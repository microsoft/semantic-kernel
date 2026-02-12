# Get Started with Semantic Kernel for Node.js/TypeScript

Highlights

- Flexible Agent Framework: build, orchestrate, and deploy AI agents and multi-agent systems
- Multi-Agent Systems: Model workflows and collaboration between AI specialists
- Plugin Ecosystem: Extend with TypeScript, OpenAPI, Model Context Protocol (MCP), and more
- LLM Support: OpenAI, Azure OpenAI, Hugging Face, Mistral, Google AI, ONNX, Ollama, NVIDIA NIM, and others
- Vector DB Support: Azure AI Search, Elasticsearch, Chroma, and more
- Process Framework: Build structured business processes with workflow modeling
- Multimodal: Text, vision, audio

## Quick Install

```bash
npm install semantic-kernel
# or
yarn add semantic-kernel
# or
pnpm add semantic-kernel
```

Supported Platforms:

- Node.js: 18+
- TypeScript: 5.0+
- OS: Windows, macOS, Linux

## 1. Setup API Keys

Set as environment variables, or create a .env file at your project root:

```bash
OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL_ID=...
...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=...
...
```

You can also override environment variables by explicitly passing configuration parameters to the AI service constructor:

```typescript
const chatService = new AzureChatCompletion({
  apiKey: '...',
  endpoint: '...',
  deploymentName: '...',
  apiVersion: '...',
})
```

## 2. Use the Kernel for Prompt Engineering

Create prompt functions and invoke them via the `Kernel`:

```typescript
import { Kernel } from 'semantic-kernel'
import { OpenAIChatCompletion } from 'semantic-kernel/connectors/ai/openai'

const kernel = new Kernel()

const chatCompletion = new OpenAIChatCompletion({
  apiKey: process.env.OPENAI_API_KEY,
  aiModelId: 'gpt-3.5-turbo',
})

kernel.addService('chat-completion', chatCompletion)

const prompt = `
1) A robot may not injure a human being...
2) A robot must obey orders given it by human beings...
3) A robot must protect its own existence...

Give me the TLDR in exactly {{$num_words}} words.`

async function main() {
  const result = await kernel.invokePrompt({
    prompt,
    arguments: { num_words: 5 },
  })

  // Get the text content from the first message
  const message = result?.value?.[0]
  const textContent = message?.items?.[0]
  console.log(textContent?.text)
}

main()
// Output: Protect humans, obey, self-preserve, prioritized.
```

## 3. Directly Use AI Services (No Kernel Required)

You can use the AI service classes directly for advanced workflows:

```typescript
import { OpenAIChatCompletion } from 'semantic-kernel/connectors/ai/openai'
import { ChatHistory } from 'semantic-kernel/contents'

async function main() {
  const service = new OpenAIChatCompletion()
  const settings = {
    temperature: 0.7,
    maxTokens: 150,
  }

  const chatHistory = new ChatHistory({
    systemMessage: 'You are a helpful assistant.',
  })
  chatHistory.addUserMessage('Write a haiku about Semantic Kernel.')

  const response = await service.getChatMessageContent({
    chatHistory,
    settings,
  })
  console.log(response.content)

  /*
    Output:

    Thoughts weave through context,  
    Semantic threads interlace—  
    Kernel sparks meaning.
    */
}

main()
```

## 4. Build an Agent with Plugins and Tools

Enhance your agent with custom tools (plugins) and structured output:

```typescript
import { ChatCompletionAgent } from 'semantic-kernel/agents'
import { AzureChatCompletion } from 'semantic-kernel/connectors/ai/azure-openai'
import { kernelFunction } from 'semantic-kernel/functions'

class MenuPlugin {
  @kernelFunction({
    description: 'Provides a list of specials from the menu.',
  })
  getSpecials(): string {
    return `
        Special Soup: Clam Chowder
        Special Salad: Cobb Salad
        Special Drink: Chai Tea
        `
  }

  @kernelFunction({
    description: 'Provides the price of the requested menu item.',
  })
  getItemPrice(menuItem: string): string {
    return '$9.99'
  }
}

interface MenuItem {
  price: number
  name: string
}

async function main() {
  // Configure structured outputs format
  const settings = {
    responseFormat: MenuItem,
  }

  // Create agent with plugin and settings
  const agent = new ChatCompletionAgent({
    service: new AzureChatCompletion(),
    name: 'SK-Assistant',
    instructions: 'You are a helpful assistant.',
    plugins: [new MenuPlugin()],
    arguments: { settings },
  })

  const response = await agent.getResponse('What is the price of the soup special?')
  console.log(response.content)

  // Output:
  // The price of the Clam Chowder, which is the soup special, is $9.99.
}

main()
```

## 5. Multi-Agent Orchestration

Coordinate a group of agents to iteratively solve a problem or refine content together:

```typescript
import { ChatCompletionAgent, GroupChatOrchestration, RoundRobinGroupChatManager } from 'semantic-kernel/agents'
import { InProcessRuntime } from 'semantic-kernel/agents/runtime'
import { AzureChatCompletion } from 'semantic-kernel/connectors/ai/azure-openai'

function getAgents() {
  return [
    new ChatCompletionAgent({
      name: 'Writer',
      instructions: 'You are a creative content writer. Generate and refine slogans based on feedback.',
      service: new AzureChatCompletion(),
    }),
    new ChatCompletionAgent({
      name: 'Reviewer',
      instructions: 'You are a critical reviewer. Provide detailed feedback on proposed slogans.',
      service: new AzureChatCompletion(),
    }),
  ]
}

async function main() {
  const agents = getAgents()
  const groupChat = new GroupChatOrchestration({
    members: agents,
    manager: new RoundRobinGroupChatManager({ maxRounds: 5 }),
  })

  const runtime = new InProcessRuntime()
  runtime.start()

  const result = await groupChat.invoke({
    task: 'Create a slogan for a new electric SUV that is affordable and fun to drive.',
    runtime,
  })

  const value = await result.get()
  console.log(`Final Slogan: ${value}`)

  // Example Output:
  // Final Slogan: "Feel the Charge: Adventure Meets Affordability in Your New Electric SUV!"

  await runtime.stopWhenIdle()
}

main()
```

## 6. Stream Responses for Real-Time Output

Get streaming responses for better user experience:

```typescript
import { Kernel } from 'semantic-kernel'
import { OpenAIChatCompletion } from 'semantic-kernel/connectors/ai/openai'

const kernel = new Kernel()
kernel.addService('chat', new OpenAIChatCompletion())

async function main() {
  const prompt = 'Write a short story about a robot learning to paint.'

  for await (const chunk of kernel.invokePromptStream({ prompt })) {
    if (Array.isArray(chunk)) {
      for (const part of chunk) {
        process.stdout.write(part.content || '')
      }
    }
  }
}

main()
```

## More Examples & Samples

Additional samples and examples are coming soon.

## Semantic Kernel Documentation

- [Getting Started with Semantic Kernel](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide)
- [Agent Framework Guide](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/)
- [Process Framework Guide](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/process/process-framework)

## TypeScript-Specific Features

### Type Safety

Semantic Kernel for Node.js/TypeScript provides full type safety:

```typescript
import type { KernelFunction, KernelArguments, FunctionResult } from 'semantic-kernel'

async function invokeWithTypes(
  kernel: Kernel,
  func: KernelFunction,
  args: KernelArguments
): Promise<FunctionResult | null> {
  return await kernel.invoke({ function: func, arguments: args })
}
```

### Async/Await and Promises

All asynchronous operations use modern async/await patterns:

```typescript
// Sequential execution
const result1 = await kernel.invoke({ functionName: 'func1', pluginName: 'plugin1' })
const result2 = await kernel.invoke({ functionName: 'func2', pluginName: 'plugin1' })

// Parallel execution
const [result1, result2] = await Promise.all([
  kernel.invoke({ functionName: 'func1', pluginName: 'plugin1' }),
  kernel.invoke({ functionName: 'func2', pluginName: 'plugin1' }),
])
```

### Decorators

Use TypeScript decorators for cleaner plugin definitions:

```typescript
import { kernelFunction, kernelParameter } from 'semantic-kernel/functions'

class MathPlugin {
  @kernelFunction({ description: 'Adds two numbers' })
  add(
    @kernelParameter({ description: 'First number' }) a: number,
    @kernelParameter({ description: 'Second number' }) b: number
  ): number {
    return a + b
  }
}
```

## Contributing

We welcome contributions! Please see our [contributing guidelines](../CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
