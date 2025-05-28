# Get Started with Semantic Kernel Python

Highlights
- Flexible Agent Framework: build, orchestrate, and deploy AI agents and multi-agent systems
- Multi-Agent Systems: Model workflows and collaboration between AI specialists
- Plugin Ecosystem: Extend with Python, OpenAPI, Model Context Protocol (MCP), and more
- LLM Support: OpenAI, Azure OpenAI, Hugging Face, Mistral, Vertex AI, ONNX, Ollama, NVIDIA NIM, and others
- Vector DB Support: Azure AI Search, Elasticsearch, Chroma, and more
- Process Framework: Build structured business processes with workflow modeling
- Multimodal: Text, vision, audio

## Quick Install

```bash
pip install --upgrade semantic-kernel
# Optional: Add integrations
pip install --upgrade semantic-kernel[hugging_face]
pip install --upgrade semantic-kernel[all]
```

Supported Platforms:
- Python: 3.10+
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

```python
chat_service = AzureChatCompletion(
    api_key=...,
    endpoint=...,
    deployment_name=...,
    api_version=...,
)
```

See the following [setup guide](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/concepts/setup) for more information.

## 2. Use the Kernel for Prompt Engineering

Create prompt functions and invoke them via the `Kernel`:

```python
import asyncio
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import KernelArguments

kernel = Kernel()
kernel.add_service(OpenAIChatCompletion())

prompt = """
1) A robot may not injure a human being...
2) A robot must obey orders given it by human beings...
3) A robot must protect its own existence...

Give me the TLDR in exactly {{$num_words}} words."""


async def main():
    result = await kernel.invoke_prompt(prompt, arguments=KernelArguments(num_words=5))
    print(result)


asyncio.run(main())
# Output: Protect humans, obey, self-preserve, prioritized.
```

## 3. Directly Use AI Services (No Kernel Required)

You can use the AI service classes directly for advanced workflows:

```python
import asyncio
import asyncio

from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.contents import ChatHistory


async def main():
    service = OpenAIChatCompletion()
    settings = OpenAIChatPromptExecutionSettings()

    chat_history = ChatHistory(system_message="You are a helpful assistant.")
    chat_history.add_user_message("Write a haiku about Semantic Kernel.")
    response = await service.get_chat_message_content(chat_history=chat_history, settings=settings)
    print(response.content)

    """
    Output:

    Thoughts weave through context,  
    Semantic threads interlace—  
    Kernel sparks meaning.
    """


asyncio.run(main())
```

## 4. Build an Agent with Plugins and Tools

Add Python functions as plugins or Pydantic models as structured outputs;

Enhance your agent with custom tools (plugins) and structured output:

```python
import asyncio
from typing import Annotated
from pydantic import BaseModel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.functions import kernel_function, KernelArguments

class MenuPlugin:
    @kernel_function(description="Provides a list of specials from the menu.")
    def get_specials(self) -> Annotated[str, "Returns the specials from the menu."]:
        return """
        Special Soup: Clam Chowder
        Special Salad: Cobb Salad
        Special Drink: Chai Tea
        """

    @kernel_function(description="Provides the price of the requested menu item.")
    def get_item_price(
        self, menu_item: Annotated[str, "The name of the menu item."]
    ) -> Annotated[str, "Returns the price of the menu item."]:
        return "$9.99"

class MenuItem(BaseModel):
    # Used for structured outputs
    price: float
    name: str

async def main():
    # Configure structured outputs format
    settings = OpenAIChatPromptExecutionSettings()
    settings.response_format = MenuItem

    # Create agent with plugin and settings
    agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="SK-Assistant",
        instructions="You are a helpful assistant.",
        plugins=[MenuPlugin()],
        arguments=KernelArguments(settings)
    )

    response = await agent.get_response("What is the price of the soup special?")
    print(response.content)

    # Output:
    # The price of the Clam Chowder, which is the soup special, is $9.99.

asyncio.run(main()) 
```

You can explore additional getting started agent samples [here](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/getting_started_with_agents).

## 5. Multi-Agent Orchestration

Coordinate a group of agents to iteratively solve a problem or refine content together:

```python
import asyncio
from semantic_kernel.agents import ChatCompletionAgent, GroupChatOrchestration, RoundRobinGroupChatManager
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

def get_agents():
    return [
        ChatCompletionAgent(
            name="Writer",
            instructions="You are a creative content writer. Generate and refine slogans based on feedback.",
            service=AzureChatCompletion(),
        ),
        ChatCompletionAgent(
            name="Reviewer",
            instructions="You are a critical reviewer. Provide detailed feedback on proposed slogans.",
            service=AzureChatCompletion(),
        ),
    ]

async def main():
    agents = get_agents()
    group_chat = GroupChatOrchestration(
        members=agents,
        manager=RoundRobinGroupChatManager(max_rounds=5),
    )
    runtime = InProcessRuntime()
    runtime.start()
    result = await group_chat.invoke(
        task="Create a slogan for a new electric SUV that is affordable and fun to drive.",
        runtime=runtime,
    )
    value = await result.get()
    print(f"Final Slogan: {value}")

    # Example Output:
    # Final Slogan: "Feel the Charge: Adventure Meets Affordability in Your New Electric SUV!"

    await runtime.stop_when_idle()

if __name__ == "__main__":
    asyncio.run(main())
```

For orchestration-focused examples, see [these orchestration samples](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/getting_started_with_agents/multi_agent_orchestration).

## More Examples & Notebooks

- [Getting Started with Agents](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/getting_started_with_agents): Practical agent orchestration and tool use  
- [Getting Started with Processes](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/getting_started_with_processes): Modeling structured workflows with the Process framework  
- [Concept Samples](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/concepts): Advanced scenarios, integrations, and SK patterns  
- [Getting Started Notebooks](https://github.com/microsoft/semantic-kernel/tree/main/python/samples/getting_started): Interactive Python notebooks for rapid experimentation  

## Semantic Kernel Documentation

- [Getting Started with Semantic Kernel Python](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide?pivots=programming-language-python)  
- [Agent Framework Guide](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/?pivots=programming-language-python)  
- [Process Framework Guide](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/process/process-framework)