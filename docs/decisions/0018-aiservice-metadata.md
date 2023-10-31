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

Developers need to be able to know more information about the `IAIService` that will eb used to execute a semantic function or a plan.
Some examples of why they need this information:

1. As an SK developer I want to write a `IAIServiceSelector` which allows me to select the OpenAI service to used based on the configured model id so that I cna select the optimum (could eb cheapest) model to use based on the prompt I am executing.
2. As an SK developer I want to write a pre-invocation hook which will compute the token size of a prompt before the prompt is sent to the LLM, so that I can determine the optimum `IAIService` to use. The library I am using to compute the token size of the prompt requires the model id.


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

var service = kernel.GetService<IChatCompletion>("OpenAIChat");
```

For Azure OpenAI we create the service with a deployment name. This is an arbitrary name specified by the person who deployed the AI model e.g. it could be `eastus-gpt-4` or `foo-bar`.
For OpenAI we create the service with a model id. This must match one of the deployed OpenAI models.

From the perspective of a prompt creator using OpenAI, they will typically tune their prompts based on the model. So when the prompt is executed we need to be able to retrieve the service using the model id. As shown in the code snippet above the `IKernel` only supports retrieving an `IAService` instance by id. Additionally the `IChatCompletion` is a generic interface so it doesn't contain any properties which provide information about a specific connector instance.

## Decision Drivers

* We need a mechanism to store generic metadata for an `IAIService` instance.
  * It will be the responsibility of the concrete `IAIService` instance to store the metadata that is relevant e.g., model id for OpenAI and HuggingFace AI services.
* We need to be able to iterate over the available `IAIService` instances.

## Considered Options

* {title of option 1}

## Decision Outcome

Chosen option: "{title of option 1}", because
{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}.
