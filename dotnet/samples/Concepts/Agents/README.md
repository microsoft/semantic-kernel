# Semantic Kernel: Agent syntax examples
This project contains a collection of examples on how to use _Semantic Kernel Agents_.

#### NuGet:
- [Microsoft.SemanticKernel.Agents.Abstractions](https://www.nuget.org/packages/Microsoft.SemanticKernel.Agents.Abstractions)
- [Microsoft.SemanticKernel.Agents.Core](https://www.nuget.org/packages/Microsoft.SemanticKernel.Agents.Core)
- [Microsoft.SemanticKernel.Agents.OpenAI](https://www.nuget.org/packages/Microsoft.SemanticKernel.Agents.OpenAI)

#### Source
- [Semantic Kernel Agent Framework](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/Agents)

The examples can be run as integration tests but their code can also be copied to stand-alone programs.

## Examples

The concept agents examples are grouped by prefix:

Prefix|Description
---|---
FoundryPromptAgent|How to use a `ChatCompletionAgent` with a [Microsoft Foundry Prompt Agent](https://learn.microsoft.com/azure/ai-foundry/agents/overview).
MixedChat|How to combine different agent types.
ComplexChat|How to develop complex agent chat solutions.
Legacy|How to use the legacy _Experimental Agent API_.

## Legacy Agents

Support for the OpenAI Assistant API was originally published in `Microsoft.SemanticKernel.Experimental.Agents` package:
[Microsoft.SemanticKernel.Experimental.Agents](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/Experimental/Agents)

This package was superseded by _Semantic Kernel Agents_. OpenAI shut down the Assistants API on August 26, 2026, so the Open AI Assistant agent was removed. The `FoundryPromptAgent` samples show the replacement: a Microsoft Foundry Prompt Agent used through a `ChatCompletionAgent`.

## Running Examples
Examples may be explored and ran within _Visual Studio_ using _Test Explorer_.

You can also run specific examples via the command-line by using test filters (`dotnet test --filter`). Type `dotnet test --help` at the command line for more details.

Example:
    
```
dotnet test --filter FoundryPromptAgent_ChartMaker
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

5. Or Azure Open AI:

    ```
    dotnet user-secrets set "AzureOpenAI:DeploymentName" "..."
    dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "..."
    dotnet user-secrets set "AzureOpenAI:Endpoint" "https://... .openai.azure.com/"
    dotnet user-secrets set "AzureOpenAI:ApiKey" "..."
    ```

6. The `FoundryPromptAgent` and `MixedChat` examples also require a Microsoft Foundry project (authenticated with the Azure CLI):

    ```
    dotnet user-secrets set "AzureAI:Endpoint" "https://... .services.ai.azure.com/api/projects/..."
    dotnet user-secrets set "AzureAI:ChatModelId" "gpt-4o"
    ```

> NOTE: Azure secrets will take precedence, if both Open AI and Azure Open AI secrets are defined, unless `ForceOpenAI` is set:

```
protected override bool ForceOpenAI => true;
```
