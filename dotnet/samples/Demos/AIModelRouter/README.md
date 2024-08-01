# AI Model Router

This sample demonstrates how to use the AI Model Router to route requests to different AI models based on the user's input.

This sample uses LMStudio, Ollama and OpenAI as the AI models and the OpenAI Connector because LMStudio and Ollama provide OpenAI API compatibility.

> [!IMPORTANT]
> You can modify to use any other combination of connector or OpenAI compatible API model provider.

## Semantic Kernel Features Used

- [Chat Completion Service](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/IChatCompletionService.cs) - Using the Chat Completion Service [OpenAI Connector implementation](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Connectors/Connectors.OpenAI/ChatCompletion/OpenAIChatCompletionService.cs) to generate responses from the LLM.
- [Filters](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/AI/ChatCompletion/IChatCompletionService.cs) - Using the Chat Completion Service [OpenAI Connector implementation](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Connectors/Connectors.OpenAI/ChatCompletion/OpenAIChatCompletionService.cs) to generate responses from the LLM.


