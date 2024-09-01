---
runme:
  document:
    relativePath: README.md
  session:
    id: 01J6KPJ8XM6CDP9YHD1ZQR868H
    updated: 2024-08-31 07:55:26Z
---

# Semantic Kernel Agents - Getting Started

This project contains a step by step guide to get started with  _Semantic Kernel Agents_.

 NuGet:

- [Microsoft.SemanticKernel.Agents.Abstractions](ht***********************************************************************ns)
- [Microsoft.SemanticKernel.Agents.Core](ht***************************************************************re)
- [Microsoft.SemanticKernel.Agents.OpenAI](ht*****************************************************************AI)

 Source

- [Semantic Kernel Agent Framework](ht********************************************************************ts)

The examples can be run as integration tests but their code can also be copied to stand-alone programs.

## Examples

The getting started with agents examples include:

Example|Description
---|---
[St*******nt](ht*********************************************************************************************************cs)|How to create and use an agent.
[St*********ns](ht***********************************************************************************************************cs)|How to associate plug-ins with an agent.
[St******at](ht********************************************************************************************************cs)|How to create a conversation between agents.
[St**************************es](ht****************************************************************************************************************************cs)|How to utilize a `KernelFunction` as a _chat strategy_.
[St************lt](ht**************************************************************************************************************cs)|How to have an agent produce JSON.
[St*********************on](ht***********************************************************************************************************************cs)|How to define dependency injection patterns for agents.
[St*****************nt](ht*******************************************************************************************************************cs)|How to create an Open AI Assistant agent.

## Legacy Agents

Support for the OpenAI Assistant API was originally published in `Microsoft.SemanticKernel.Experimental.Agents` package:
[Microsoft.SemanticKernel.Experimental.Agents](ht*********************************************************************************ts)

This package has been superseded by _Semantic Kernel Agents_, which includes support for Open AI Assistant agents.

## Running Examples with Filters

Examples may be explored and ran within _Visual Studio_ using _Test Explorer_.

You can also run specific examples via the command-line by using test filters (`dotnet test --filter`). Type `dotnet test --help` at the command line for more details.

Example:

```sh {"id":"01J6KPX0GQCZXPP6FDPQ50PNZM"}
dotnet test --filter St******at
```

## Configuring Secrets

Each example requires secrets / credentials to access OpenAI or Azure OpenAI.

We suggest using .NET [Secret Manager](ht**************************************************************ts) to avoid the risk of leaking secrets into the repository, branches and pull requests. You can also use environment variables if you prefer.

To set your secrets with .NET Secret Manager:

1. Navigate the console to the project folder:

```sh {"id":"01J6KPX0GQCZXPP6FDPR1WAZZ2"}
cd dotnet/samples/GettingStartedWithAgents
```

2. Examine existing secret definitions:

```sh {"id":"01J6KPX0GQCZXPP6FDPTYW38M3"}
dotnet user-secrets list
```

3. If needed, perform first time initialization:

```sh {"id":"01J6KPX0GQCZXPP6FDPY0GECXC"}
dotnet user-secrets init
```

4. Define secrets for either Open AI:

```sh {"id":"01J6KPX0GQCZXPP6FDQ12BV6M9"}
dotnet user-secrets set "OpenAI:ChatModelId" "..."
dotnet user-secrets set "OpenAI:ApiKey" "..."
```

5. Or Azure Open AI:

```sh {"id":"01J6KPX0GQCZXPP6FDQ290W7XP"}
dotnet user-secrets set "AzureOpenAI:DeploymentName" "..."
dotnet user-secrets set "AzureOpenAI:ChatDeploymentName" "..."
dotnet user-secrets set "AzureOpenAI:Endpoint" "https://... .openai.azure.com/"
dotnet user-secrets set "AzureOpenAI:ApiKey" "..."
```

> NOTE: Azure secrets will take precedence, if both Open AI and Azure Open AI secrets are defined, unless `ForceOpenAI` is set:

```sh {"id":"01J6KPX0GQCZXPP6FDQ68Q18B3"}
protected override bool ForceOpenAI => true;
```
