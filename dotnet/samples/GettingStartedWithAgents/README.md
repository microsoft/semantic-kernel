# Semantic Kernel Agents - Getting Started

This project contains a step by step guide to get started with  _Semantic Kernel Agents_.

## NuGet

- [Microsoft.SemanticKernel.Agents.Abstractions](https://www.nuget.org/packages/Microsoft.SemanticKernel.Agents.Abstractions)
- [Microsoft.SemanticKernel.Agents.Core](https://www.nuget.org/packages/Microsoft.SemanticKernel.Agents.Core)
- [Microsoft.SemanticKernel.Agents.OpenAI](https://www.nuget.org/packages/Microsoft.SemanticKernel.Agents.OpenAI)

## Source

- [Semantic Kernel Agent Framework](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/Agents)

The examples can be run as integration tests but their code can also be copied to stand-alone programs.

## Examples

The getting started with agents examples include:

### ChatCompletion

Example|Description
---|---
[Step01_Agent](./dotnet/samples/GettingStartedWithAgents/Step01_Agent.cs)|How to create and use an agent.
[Step02_Plugins](./dotnet/samples/GettingStartedWithAgents/Step02_Plugins.cs)|How to associate plug-ins with an agent.
[Step03_Chat](./dotnet/samples/GettingStartedWithAgents/Step03_Chat.cs)|How to create a conversation between agents.
[Step04_KernelFunctionStrategies](./dotnet/samples/GettingStartedWithAgents/Step04_KernelFunctionStrategies.cs)|How to utilize a `KernelFunction` as a _chat strategy_.
[Step05_JsonResult](./dotnet/samples/GettingStartedWithAgents/Step05_JsonResult.cs)|How to have an agent produce JSON.
[Step06_DependencyInjection](./dotnet/samples/GettingStartedWithAgents/Step06_DependencyInjection.cs)|How to define dependency injection patterns for agents.
[Step07_Telemetry](./dotnet/samples/GettingStartedWithAgents/Step07_Telemetry.cs)|How to enable logging for agents.

### Open AI Assistant

Example|Description
---|---
[Step01_Assistant](./dotnet/samples/GettingStartedWithAgents/OpenAIAssistant/Step01_Assistant.cs)|How to create an Open AI Assistant agent.
[Step02_Assistant_Plugins](./dotnet/samples/GettingStartedWithAgents/OpenAIAssistant/Step02_Assistant_Plugins.cs)|How to associate plug-ins with an Open AI Assistant agent.
[Step03_Assistant_Vision](./dotnet/samples/GettingStartedWithAgents/OpenAIAssistant/Step03_Assistant_Vision.cs)|How to provide an image as input to an Open AI Assistant agent.
[Step04_AssistantTool_CodeInterpreter_](./dotnet/samples/GettingStartedWithAgents/OpenAIAssistant/Step04_AssistantTool_CodeInterpreter.cs)|How to use the code-interpreter tool for an Open AI Assistant agent.
[Step05_AssistantTool_FileSearch](./dotnet/samples/GettingStartedWithAgents/OpenAIAssistant/Step05_AssistantTool_FileSearch.cs)|How to use the file-search tool for an Open AI Assistant agent.

### Azure AI Agent

Example|Description
---|---
[Step01_AzureAIAgent](./dotnet/samples/GettingStartedWithAgents/AzureAIAgent/Step01_AzureAIAgent.cs)|How to create an `AzureAIAgent`.
[Step02_AzureAIAgent_Plugins](./dotnet/samples/GettingStartedWithAgents/AzureAIAgent/Step02_AzureAIAgent_Plugins.cs)|How to create an `AzureAIAgent`.
[Step03_AzureAIAgent_Chat](./dotnet/samples/GettingStartedWithAgents/AzureAIAgent/Step03_AzureAIAgent_Chat.cs)|How create a conversation with `AzureAIAgent`s.
[Step04_AzureAIAgent_CodeInterpreter](./dotnet/samples/GettingStartedWithAgents/AzureAIAgent/Step04_AzureAIAgent_CodeInterpreter.cs)|How to use the code-interpreter tool for an `AzureAIAgent`.
[Step05_AzureAIAgent_FileSearch](./dotnet/samples/GettingStartedWithAgents/AzureAIAgent/Step05_AzureAIAgent_FileSearch.cs)|How to use the file-search tool for an `AzureAIAgent`.
[Step06_AzureAIAgent_OpenAPI](./dotnet/samples/GettingStartedWithAgents/AzureAIAgent/Step06_AzureAIAgent_OpenAPI.cs)|How to use the Open API tool for an `AzureAIAgent`.

### Bedrock Agent

Example|Description
---|---
[Step01_BedrockAgent](./BedrockAgent/Step01_BedrockAgent.cs)|How to create a `BedrockAgent` and interact with it in the most basic way.
[Step02_BedrockAgent_CodeInterpreter](./BedrockAgent/Step02_BedrockAgent_CodeInterpreter.cs)|How to use the code-interpreter tool with a `BedrockAgent`.
[Step03_BedrockAgent_Functions](./BedrockAgent/Step03_BedrockAgent_Functions.cs)|How to use kernel functions with a `BedrockAgent`.
[Step04_BedrockAgent_Trace](./BedrockAgent/Step04_BedrockAgent_Trace.cs)|How to enable tracing for a `BedrockAgent` to inspect the chain of thoughts.
[Step05_BedrockAgent_FileSearch](./BedrockAgent/Step05_BedrockAgent_FileSearch.cs)|How to use file search with a `BedrockAgent` (i.e. Bedrock knowledge base).
[Step06_BedrockAgent_AgentChat](./BedrockAgent/Step06_BedrockAgent_AgentChat.cs)|How to create a conversation between two agents and one of them in a `BedrockAgent`.

### CopilotStudio Agent

Example|Description
---|---
[Step01_CopilotStudioAgent](./CopilotStudioAgent/Step01_CopilotStudioAgent.cs)|How to create a `CopilotStudioAgent` and interact with it in the most basic way.
[Step02_CopilotStudioAgent_Thread](./CopilotStudioAgent/Step02_CopilotStudioAgent_Thread.cs)|How to use `CopilotStudioAgent` with an `AgentThread`.
[Step03_CopilotStudioAgent_WebSearch](./CopilotStudioAgent/Step03_CopilotStudioAgent_WebSearch.cs)|How to use `CopilotStudioAgent` with web-search enabled.

### Orchestration

Example|Description
---|---
[Step01_Concurrent](./Orchestration/Step01_Concurrent.cs)|How to use a concurrent orchestration..
[Step01a_ConcurrentWithStructuredOutput](./Orchestration/Step01a_ConcurrentWithStructuredOutput.cs)|How to use structured output (with concurrent orchestration).
[Step02_Sequential](./Orchestration/Step02_Sequential.cs)|How to use sequential orchestration.
[Step02a_Sequential](./Orchestration/Step02a_Sequential.cs)|How to cancel an orchestration (with sequential orchestration).
[Step03_GroupChat](./Orchestration/Step03_GroupChat.cs)|How to use group-chat orchestration.
[Step03a_GroupChatWithHumanInTheLoop](./Orchestration/Step03a_GroupChatWithHumanInTheLoop.cs)|How to use group-chat orchestration with human in the loop.
[Step03b_GroupChatWithAIManager](./Orchestration/Step03b_GroupChatWithAIManager.cs)|How to use group-chat orchestration with a AI powered group-manager.
[Step04_Handoff](./Orchestration/Step04_Handoff.cs)|How to use handoff orchestration.
[Step04b_HandoffWithStructuredInput](./Orchestration/Step04b_HandoffWithStructuredInput.cs)|How to use structured input (with handoff orchestration).

## Legacy Agents

Support for the OpenAI Assistant API was originally published in `Microsoft.SemanticKernel.Experimental.Agents` package:
[Microsoft.SemanticKernel.Experimental.Agents](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/Experimental/Agents)

This package has been superseded by _Semantic Kernel Agents_, which includes support for Open AI Assistant agents.

## Running Examples with Filters

Examples may be explored and ran within _Visual Studio_ using _Test Explorer_.

You can also run specific examples via the command-line by using test filters (`dotnet test --filter`). Type `dotnet test --help` at the command line for more details.

Example:

```
dotnet test --filter Step3_Chat
```

## Configuring Secrets

Each example requires secrets / credentials to access OpenAI or Azure OpenAI.

We suggest using .NET [Secret Manager](https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets) to avoid the risk of leaking secrets into the repository, branches and pull requests. You can also use environment variables if you prefer.

To set your secrets with .NET Secret Manager:

1. Navigate the console to the project folder:

    ```
    cd dotnet/samples/GettingStartedWithAgents
    ```

2. Examine existing secret definitions:

    ```
    dotnet user-secrets list
    ```

3. If needed, perform first time initialization:

    ```
    dotnet user-secrets init
    ```

4. Define secrets for either Open AI:

    ```
    dotnet user-secrets set "OpenAI:ChatModelId" "..."
    dotnet user-secrets set "OpenAI:ApiKey" "..."
    ```

5. Or Azure OpenAI:

    ```
    dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "gpt-4o"
    dotnet user-secrets set "AzureOpenAI:Endpoint" "https://... .openai.azure.com/"
    dotnet user-secrets set "AzureOpenAI:ApiKey" "..."
    ```

6. Or Azure AI:

    ```
    dotnet user-secrets set "AzureAI:Endpoint" "..."
    dotnet user-secrets set "AzureAI:ChatModelId" "gpt-4o"
    ```

7. Or Bedrock:

    ```
    dotnet user-secrets set "BedrockAgent:AgentResourceRoleArn" "arn:aws:iam::...:role/..."
    dotnet user-secrets set "BedrockAgent:FoundationModel" "..."
    ```

> NOTE: Azure secrets will take precedence, if both Open AI and Azure OpenAI secrets are defined, unless `ForceOpenAI` is set:

```
protected override bool ForceOpenAI => true;
```
