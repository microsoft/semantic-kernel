---
# These are optional elements. Feel free to remove any of them.
status: {proposed}
date: 2023-10-02
deciders: mabolan, markwallace
consulted: semenshi, dmytrostruk, rbarreto
informed: 
---
# Multiple Model Support for Semantic Functions

## Context and Problem Statement

Developers need to be able to use multiple models e.g., using chat completion together with embeddings.

<!-- This is an optional element. Feel free to remove. -->
## Use Cases

In scope for Semantic Kernel V1.0

* Select Model Request Settings by Service Id.
  * A Service Id uniquely identifies a registered AI Service and is typically defined in the scope of an application.
* Select Model Request Settings by Model Id.
  * A Model Id uniquely identifies a Large Language Model. Multiple AI service providers can support the same LLM.
* Select AI Service and Model Request Settings By Developer Defined Strategy.
  * A Developer Defined Strategy is a code first approach where a developer provides the logic.

Out of scope for V1.0

* Select Model Request Settings by Provider Id and Model Id
  * A Provider Id uniquely identifies an AI provider e.g. "Azure OpenAI", "OpenAI", "Hugging Face"

## Decision Outcome

Support just use cases listed in this ADR.

## Descriptions of the Use Cases

**Note: All code is pseudo code and does not accurately reflect what the final implementations will look like.**

### Select Model Request Settings by Service Id

_As a developer using the Semantic Kernel I can configure multiple request settings for a semantic function and associate each one with a service id so that the correct request settings are used when different services are used to execute my semantic function._

The semantic function template configuration allows multiple model request settings to be configured. In this case the developer configures different settings based on the service id that is used to execute the semantic function.
In the example below the semantic function is executed with "OpenAIChat" using `max_tokens=240` because "OpenAIChat" is set as the default AI service.

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

### Select Model Request Settings by Model Id

_As a developer using the Semantic Kernel I can configure multiple request settings for a semantic function and associate each one with a model id so that the correct request settings are used when different LLM's are used to execute my semantic function._

In this case the developer configures different settings based on the model id that is used to execute the semantic function.
In the example below the semantic function is executed with "OpenAIText" using `max_tokens=60` because "OpenAIText" is set as the default AI service.
If "AzureText" was set as the default AI service, the  `max_tokens=60` would also be used if the deployment name matches the model id. [For Azure OpenAI the deployment name is used in code to call the model by using the client libraries and the REST APIs](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/create-resource?pivots=web-portal#deploy-a-model).

**Note** For Azure OpenAI When registering an AI Service the `modelId` argument is optional (and a new argument). If none is provided the `deploymentName` is used instead. Because the `deploymentName` name can be set to anything this may not work. Developers can use the Azure API to query for the `modelId` associated with a deployment so that it is correctly set when registering the AI service.

```csharp
// Configure a Kernel with multiple LLM's
IKernel kernel = Kernel.Builder
    .WithLoggerFactory(ConsoleLogger.LoggerFactory)
    .WithAzureTextCompletionService(deploymentName: aoai.DeploymentName, modelId: aoai.ModelId,// text-davinci-003
        endpoint: aoai.Endpoint, serviceId: "AzureText", apiKey: aoai.ApiKey)
    .WithAzureChatCompletionService(deploymentName: aoai.ChatDeploymentName, modelId: aoai.ModelId, // gpt-35-turbo
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
    { ""model_id"": ""text-davinci-003"", ""max_tokens"": 60 },
    { ""model_id"": ""gpt-35-turbo"", ""max_tokens"": 120 },
    { ""model_id"": ""gpt-3.5-turbo"", ""max_tokens"": 180 }
  ]
}";
var templateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);
var func = kernel.CreateSemanticFunction(prompt, config: templateConfig!, "HelloAI");

// Semantic function is executed with OpenAIText using max_tokens=60
result = await kernel.RunAsync(func);
```

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
    { ""model_id"": ""text-davinci-003"", ""max_tokens"": 60 },
    { ""model_id"": ""gpt-35-turbo"", ""max_tokens"": 120 },
    { ""model_id"": ""gpt-3.5-turbo"", ""max_tokens"": 180 }
  ]
}";
var templateConfig = JsonSerializer.Deserialize<PromptTemplateConfig>(configPayload);
var func = kernel.CreateSemanticFunction(prompt, config: templateConfig!, "HelloAI");

// Semantic function is executed with AI Service returned by custom AIService factory
var funcOptions = new FunctionOptions();
funcOptions.AddFactory<IAIService>(myAiServiceFactory);
funcOptions.AddFactory<AIRequestSettings>(myRequestSettingsFactory);
result = await kernel.RunAsync(func, funcVariables, funcOptions);
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
