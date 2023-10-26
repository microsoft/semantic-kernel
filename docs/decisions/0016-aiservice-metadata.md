---
# These are optional elements. Feel free to remove any of them.
status: {proposed}
date: {2023-10-25}
deciders: semenshi, markwallace, rbarreto, dmytrostruk
consulted: 
informed: 
---
# Add AI Service Metadata

## Context and Problem Statement

{Describe the context and problem statement, e.g., in free form using two to three sentences or in the form of an illustrative story.
 You may want to articulate the problem in form of a question and add links to collaboration boards or issue management systems.}

Current implementation of `IAIService` is empty.

```csharp
public interface IAIService
{
}
```

We can retrieve `IAIService` instances using `T IKernel.GetService<T>(string? name = null) where T : IAIService;` i.e., by service type and name (aka service id).
The concrete instance of an `IAIService` can have different attributes depending on the service provider e.g. Azure OpenAI has a deployment name and OpenAI services have a model id.

Consider the following code snippet:

```csharp
IKernel kernel = new KernelBuilder()
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithAzureChatCompletionService(
        deploymentName: chatDeploymentName,
        endpoint: endpoint,
        serviceId: "AzureOpenAIChat",
        apiKey: apiKey)
    .WithOpenAIChatCompletionService(
        modelId: openAIModelId,
        serviceId: "OpenAIChat",
        apiKey: openAIApiKey)
    .Build();
```

For Azure OpenAI we create the service with a deployment name. This is an arbitrary name specified by the person who deployed the AI model e.g. it could be `eastus-gpt-4` or `foo-bar`.
For OpenAI we create the service with a model id. This must match one of the deployed OpenAI models.

From the perspective of a prompt creator using OpenAI, they will typically tune their prompts based on the model. So when the prompt is executed we need to be able to retrieve the service using the model id.

```csharp
var service = kernel.GetService<IChatCompletion>("OpenAIChat");
```

The code snippet above shows the API that `IKernel` supports to retrieve an `IAService` instance.

The `IChatCompletion` is a generic interface so it doesn't contain any properties which provide information about a specific connector instance.

## Decision Drivers

* We need a mechanism to store generic metadata for an `IAIService` instance.
  * It will be the responsibility of the concrete `IAIService` instance to store the metadata that is relevant e.g., model id for OpenAI and HuggingFace AI services.
* We need to be able to iterate over the available `IAIService` instances.
* … <!-- numbers of drivers can vary -->

## Considered Options

* {title of option 1}
* {title of option 2}
* {title of option 3}
* … <!-- numbers of options can vary -->

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.
