---
# These are optional elements. Feel free to remove any of them.
status: {proposed}
date: {2023-11-10}
deciders: SergeyMenshykh, markwallace, rbarreto, dmytrostruk
consulted: 
informed: 
---
# Add AI Service Metadata

## Context and Problem Statement

Developers need to be able to know more information about the `IAIService` that will be used to execute a semantic function or a plan.
Some examples of why they need this information:

1. As an SK developer I want to write a `IAIServiceSelector` which allows me to select the OpenAI service to used based on the configured model id so that I can select the optimum (could eb cheapest) model to use based on the prompt I am executing.
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

* Option #1
  * Extend `IAIService` to include the following properties:
    * `string? ModelId { get; }` which returns the model id. It will be the responsibility of each `IAIService` implementation to populate this with the appropriate value.
    * `IReadOnlyDictionary<string, object> Attributes { get; }` which returns the attributes as a readonly dictionary. It will be the responsibility of each `IAIService` implementation to populate this with the appropriate metadata.
  * Extend `INamedServiceProvider` to include this method `ICollection<T> GetServices<T>() where T : TService;`
  * Extend `OpenAIKernelBuilderExtensions` so that `WithAzureXXX` methods will include a `modelId` property if a specific model can be targeted.
* Option #2
  * Extend `IAIService` to include the following method:
    * `T? GetAttributes<T>() where T : AIServiceAttributes;` which returns an instance of `AIServiceAttributes`. It will be the responsibility of each `IAIService` implementation to define it's own service attributes class and populate this with the appropriate values.
  * Extend `INamedServiceProvider` to include this method `ICollection<T> GetServices<T>() where T : TService;`
  * Extend `OpenAIKernelBuilderExtensions` so that `WithAzureXXX` methods will include a `modelId` property if a specific model can be targeted.
* Option #3
* Option #2
  * Extend `IAIService` to include the following properties:
    * `public IReadOnlyDictionary<string, object> Attributes => this.InternalAttributes;` which returns a read only dictionary. It will be the responsibility of each `IAIService` implementation to define it's own service attributes class and populate this with the appropriate values.
    * `ModelId`
    * `Endpoint`
    * `ApiVersion`
  * Extend `INamedServiceProvider` to include this method `ICollection<T> GetServices<T>() where T : TService;`
  * Extend `OpenAIKernelBuilderExtensions` so that `WithAzureXXX` methods will include a `modelId` property if a specific model can be targeted.

These options would be used as follows:

As an SK developer I want to write a custom `IAIServiceSelector` which will select an AI service based on the model id because I want to restrict which LLM is used.
In the sample below the service selector implementation looks for the first service that is a GPT3 model.

### Option 1

``` csharp
public class Gpt3xAIServiceSelector : IAIServiceSelector
{
    public (T?, AIRequestSettings?) SelectAIService<T>(string renderedPrompt, IAIServiceProvider serviceProvider, IReadOnlyList<AIRequestSettings>? modelSettings) where T : IAIService
    {
        var services = serviceProvider.GetServices<T>();
        foreach (var service in services)
        {
            if (!string.IsNullOrEmpty(service.ModelId) && service.ModelId.StartsWith("gpt-3", StringComparison.OrdinalIgnoreCase))
            {
                Console.WriteLine($"Selected model: {service.ModelId}");
                return (service, new OpenAIRequestSettings());
            }
        }

        throw new SKException("Unable to find AI service for GPT 3.x.");
    }
}
```

## Option 2

``` csharp
public class Gpt3xAIServiceSelector : IAIServiceSelector
{
    public (T?, AIRequestSettings?) SelectAIService<T>(string renderedPrompt, IAIServiceProvider serviceProvider, IReadOnlyList<AIRequestSettings>? modelSettings) where T : IAIService
    {
        var services = serviceProvider.GetServices<T>();
        foreach (var service in services)
        {
            var serviceModelId = service.GetAttributes<AIServiceAttributes>()?.ModelId;
            if (!string.IsNullOrEmpty(serviceModelId) && serviceModelId.StartsWith("gpt-3", StringComparison.OrdinalIgnoreCase))
            {
                Console.WriteLine($"Selected model: {serviceModelId}");
                return (service, new OpenAIRequestSettings());
            }
        }

        throw new SKException("Unable to find AI service for GPT 3.x.");
    }
}
```

## Option 3

```csharp
public (T?, AIRequestSettings?) SelectAIService<T>(string renderedPrompt, IAIServiceProvider serviceProvider, IReadOnlyList<AIRequestSettings>? modelSettings) where T : IAIService
{
    var services = serviceProvider.GetServices<T>();
    foreach (var service in services)
    {
        var serviceModelId = service.GetModelId();
        var serviceOrganization = service.GetAttribute(OpenAIServiceAttributes.OrganizationKey);
        var serviceDeploymentName = service.GetAttribute(AzureOpenAIServiceAttributes.DeploymentNameKey);
        if (!string.IsNullOrEmpty(serviceModelId) && serviceModelId.StartsWith("gpt-3", StringComparison.OrdinalIgnoreCase))
        {
            Console.WriteLine($"Selected model: {serviceModelId}");
            return (service, new OpenAIRequestSettings());
        }
    }

    throw new SKException("Unable to find AI service for GPT 3.x.");
}
```

## Decision Outcome

Chosen option: Option 1, because it's a simple implementation and allows easy iteration over all possible attributes.
