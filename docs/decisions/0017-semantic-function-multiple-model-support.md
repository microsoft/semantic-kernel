---
# These are optional elements. Feel free to remove any of them.
status: approved
contact: markwallace-microsoft
date: 2023-10-26
deciders: markwallace-microsoft, semenshi, rogerbarreto
consulted: mabolan, dmytrostruk
informed: 
---
# Multiple Model Support for Semantic Functions

## Context and Problem Statement

Developers need to be able to use multiple models e.g., using chat completion together with embeddings.

## Use Cases

In scope for Semantic Kernel V1.0

* Select Model Request Settings by Service Id.
  * A Service Id uniquely identifies a registered AI Service and is typically defined in the scope of an application.
* Select AI Service and Model Request Settings By Developer Defined Strategy.
  * A Developer Defined Strategy is a code first approach where a developer provides the logic.

Out of scope for V1.0

* Select Model Request Settings by Model Id.
  * A Model Id uniquely identifies a Large Language Model. Multiple AI service providers can support the same LLM.
* Select Model Request Settings by Provider Id and Model Id
  * A Provider Id uniquely identifies an AI provider e.g. "Azure OpenAI", "OpenAI", "Hugging Face"

## Decision Outcome

Support just use cases listed in this ADR.

## Descriptions of the Use Cases

**Note: All code is pseudo code and does not accurately reflect what the final implementations will look like.**

### Select Model Request Settings by Service Id

_As a developer using the Semantic Kernel I can configure multiple request settings for a semantic function and associate each one with a service id so that the correct request settings are used when different services are used to execute my semantic function._

The semantic function template configuration allows multiple model request settings to be configured. In this case the developer configures different settings based on the service id that is used to execute the semantic function.
In the example below the semantic function is executed with "AzureText" using `max_tokens=60` because "AzureText" is the first service id in the list of models configured for the prompt.

```csharp
// Configure a Kernel with multiple LLM's
IKernel kernel = Kernel.Builder
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithAzureTextCompletionService(deploymentName: aoai.DeploymentName,
        endpoint: aoai.Endpoint, serviceId: "AzureText", apiKey: aoai.ApiKey)
    .WithAzureChatCompletionService(deploymentName: aoai.ChatDeploymentName,
        endpoint: aoai.Endpoint, serviceId: "AzureChat", apiKey: aoai.ApiKey)
    .WithOpenAITextCompletionService(modelId: oai.ModelId,
        serviceId: "OpenAIText", apiKey: oai.ApiKey)
    .WithOpenAIChatCompletionService(modelId: oai.ChatModelId,
        serviceId: "OpenAIChat", apiKey: oai.ApiKey, setAsDefault: true)
    .Build();

// Configure semantic function with multiple LLM request settings
string configPayload = @"{
  ""schema"": 1,
  ""description"": ""Hello AI, what can you do for me?"",
  ""models"": [
    { ""service_id"": ""AzureText"", ""max_tokens"": 60 },
    { ""service_id"": ""AzureChat"", ""max_tokens"": 120 },
    { ""service_id"": ""OpenAIText"", ""max_tokens"": 180 },
    { ""service_id"": ""OpenAIChat"", ""max_tokens"": 240 }
  ]
}";
var templateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);
var func = kernel.CreateSemanticFunction(prompt, config: templateConfig!, "HelloAI");

// Semantic function is executed with OpenAIChat using max_tokens=240
result = await kernel.RunAsync(func);
```

This works by using the `IAIServiceSelector` interface as the strategy for selecting the AI service and request settings to user when invoking a semantic function.
The interface is defined as follows:

```csharp
public interface IAIServiceSelector
{
    (T?, AIRequestSettings?) SelectAIService<T>(IAIServiceProvider serviceProvider, IReadOnlyList<AIRequestSettings>? modelSettings) where T : IAIService;
}
```

A default `OrderedIAIServiceSelector` implementation is used which selects the AI service based on the order of the model request settings defined for the semantic function.
The implementation checks if a service exists which the corresponding service id and if it does it and the associated model request settings will be used.
In no model request settings are defined then the default text completion service is used.
A default set of request settings can be specified by leaving the service id undefined or empty, the first such default will be used.
If no default if specified and none of the specified services are available the operation will fail.

### Select AI Service and Model Request Settings By Developer Defined Strategy

_As a developer using the Semantic Kernel I can provide factories which select the AI service and request settings used to execute my function so that I can dynamically control which AI service is used to execute my semantic function._

In this case the developer configures different settings based on the model id and provides an AI Service factory which determines which AI Service will be used when the semantic function is executed.
In the example below the semantic function is executed with whatever AI Service `myServiceFactory` returns.

```csharp
// Configure a Kernel with multiple LLM's
IKernel kernel = Kernel.Builder
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithAzureTextCompletionService(deploymentName: aoai.DeploymentName, // text-davinci-003
        endpoint: aoai.Endpoint, serviceId: "AzureText", apiKey: aoai.ApiKey)
    .WithAzureChatCompletionService(deploymentName: aoai.ChatDeploymentName, // gpt-35-turbo
        endpoint: aoai.Endpoint, serviceId: "AzureChat", apiKey: aoai.ApiKey)
    .WithOpenAITextCompletionService(modelId: oai.ModelId, // text-davinci-003
        serviceId: "OpenAIText", apiKey: oai.ApiKey, setAsDefault: true)
    .WithOpenAIChatCompletionService(modelId: oai.ChatModelId, // gpt-3.5-turbo
        serviceId: "OpenAIChat", apiKey: oai.ApiKey)
    .Build();

// Configure semantic function with multiple LLM request settings
string configPayload = @"{
  ""schema"": 1,
  ""description"": ""Hello AI, what can you do for me?"",
  ""models"": [
    { ""max_tokens"": 60 },
    { ""max_tokens"": 120 },
    { ""max_tokens"": 180 }
  ]
}";
var templateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);
var func = kernel.CreateSemanticFunction(prompt, config: templateConfig!, "HelloAI");

// Semantic function is executed with AI Service and AI request Settings dynamically determined
result = await kernel.RunAsync(func, funcVariables);
```

## More Information

### Select AI Service by Service Id

The following use case is supported. Developers can create a `Kernel`` instance with multiple named AI services. When invoking a semantic function the service id (and optionally request settings to be used) can be specified. The named AI service will be used to execute the prompt.

```csharp
var aoai = TestConfiguration.AzureOpenAI;
var oai = TestConfiguration.OpenAI;

// Configure a Kernel with multiple LLM's
IKernel kernel = Kernel.Builder
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithAzureTextCompletionService(deploymentName: aoai.DeploymentName, 
        endpoint: aoai.Endpoint, serviceId: "AzureText", apiKey: aoai.ApiKey)
    .WithAzureChatCompletionService(deploymentName: aoai.ChatDeploymentName, 
        endpoint: aoai.Endpoint, serviceId: "AzureChat", apiKey: aoai.ApiKey)
    .WithOpenAITextCompletionService(modelId: oai.ModelId, 
        serviceId: "OpenAIText", apiKey: oai.ApiKey)
    .WithOpenAIChatCompletionService(modelId: oai.ChatModelId, 
        serviceId: "OpenAIChat", apiKey: oai.ApiKey)
    .Build();

// Invoke the semantic function and service and request settings to use
result = await kernel.InvokeSemanticFunctionAsync(prompt, 
    requestSettings: new OpenAIRequestSettings() 
        { ServiceId = "AzureText", MaxTokens = 60 });

result = await kernel.InvokeSemanticFunctionAsync(prompt, 
    requestSettings: new OpenAIRequestSettings() 
        { ServiceId = "AzureChat", MaxTokens = 120 });

result = await kernel.InvokeSemanticFunctionAsync(prompt, 
    requestSettings: new OpenAIRequestSettings() 
        { ServiceId = "OpenAIText", MaxTokens = 180 });

result = await kernel.InvokeSemanticFunctionAsync(prompt, 
    requestSettings: new OpenAIRequestSettings() 
        { ServiceId = "OpenAIChat", MaxTokens = 240 });
```
