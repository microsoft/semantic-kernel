# Semantic Kernel Agents - Getting Started

This project contains a step by step guide to get started with  _Semantic Kernel Agents_.


#### NuGet:
- [Microsoft.SemanticKernel.Agents.Abstractions](https://www.nuget.org/packages/Microsoft.SemanticKernel.Agents.Abstractions)
- [Microsoft.SemanticKernel.Agents.Core](https://www.nuget.org/packages/Microsoft.SemanticKernel.Agents.Core)
- [Microsoft.SemanticKernel.Agents.OpenAI](https://www.nuget.org/packages/Microsoft.SemanticKernel.Agents.OpenAI)

#### Source
- [Semantic Kernel Agent Framework](https://github.com/microsoft/semantic-kernel/tree/main/dotnet/src/Agents)

The examples can be run as integration tests but their code can also be copied to stand-alone programs.

## Examples

The getting started with agents examples include:

Example|Description
---|---
[Step1_Agent](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithAgents/Step1_Agent.cs)|How to create and use an agent.
[Step2_Plugins](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithAgents/Step2_Plugins.cs)|How to associate plug-ins with an agent.
[Step3_Chat](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithAgents/Step3_Chat.cs)|How to create a conversation between agents.
[Step4_KernelFunctionStrategies](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithAgents/Step4_KernelFunctionStrategies.cs)|How to utilize a `KernelFunction` as a _chat strategy_.
[Step5_JsonResult](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithAgents/Step5_JsonResult.cs)|How to have an agent produce JSON.
[Step6_DependencyInjection](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithAgents/Step6_DependencyInjection.cs)|How to define dependency injection patterns for agents.
[Step7_OpenAIAssistant](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/GettingStartedWithAgents/Step7_OpenAIAssistant.cs)|How to create an Open AI Assistant agent.

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

5. Or Azure Open AI:

    ```
    dotnet user-secrets set "AzureOpenAI:DeploymentName" "..."
    dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "..."
    dotnet user-secrets set "AzureOpenAI:Endpoint" "https://... .openai.azure.com/"
    dotnet user-secrets set "AzureOpenAI:ApiKey" "..."
    ```

> NOTE: Azure secrets will take precedence, if both Open AI and Azure Open AI secrets are defined, unless `ForceOpenAI` is set:

```
protected override bool ForceOpenAI => true;
```
