---
# These are optional elements. Feel free to remove any of them.
status: proposed
date: 2023-07-27
deciders: shawncal
consulted: 
informed: 
---
# Create Semantic Function API Pattern

## Context and Problem Statement

This ADR describes some enhancements to the current patterns used to create a Semantic Functions with the view to addressing some issues and extending the functionality to support the following use cases:

1. As a developer I want to be able to provide multiple “request settings” for a semantic function so that when my function is executed, I get the best behavior for the LLM being used.
2. As a developer I want to be able to influence the strategy used to select the LLM used to execute my prompt so that the optimum LLM used based on the available models. At a minimum I want to be able to define a list of LLM’s with preferred order.

## Decision Drivers

* Address the use cases described in the problem statement
* Support configuring multiple request settings within a prompt so prompts can be tuned to work with different AI models and versions of AI models
* Allow the semantic function lifecycle to be decoupled from the kernel lifecycle
* Support switching to a YAML based prompt format in the future
* Support for different template formats e.g., semantic kernel format, handlebars, f-string, etc.

## Considered Options

* Incremental updates to the existing code used to create semantic functions i.e., [PromptTemplateConfig](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/SemanticFunctions/PromptTemplateConfig.cs), [SemanticFunctionConfig](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/SemanticKernel.Abstractions/SemanticFunctions/SemanticFunctionConfig.cs)
* Introduce a new abstraction to define the configuration for a prompt (aka Semantic Function)

## Decision Outcome

Chosen option: Introduce a new abstraction to define the configuration for a prompt.

## More Information

### Current API Pattern
To create the semantic function the current pattern is something like this:

```csharp
IKernel kernel = Kernel.Builder
    .WithAzureChatCompletionService(deploymentName: modelId, endpoint: endpoint, apiKey: apiKey)
    .Build();

var config = new PromptTemplateConfig()
{
    Type = "completion",
    Description = "Say hello in German",
    Completion = new CompletionConfig(),
    DefaultServices = new List<string>() { "gpt-35-turbo" },
    Input = new InputConfig()
};

var function = kernel.CreateSemanticFunction(
                promptTemplate: "Say hello in German",
                config: config,
                skillName: "GermanSkill",
                functionName: "SayHello");
```

This has several issues:

1. Only supports prompt template config type of completion.
    1. It’s not clear this restriction is meaningful or required. Developers can set this and still use a semantic function with an image generation model.
1. The semantic function is created using the default template engine from the Kernel, it is added to the Kernels default skill collection and has the Kernels default text completion set on it. This links the semantic function with the kernel instance that was used to create it.
    1. There is no option provided to have different life-cycles for semantic function versus kernel instances.
    1. There is an assumption that all semantic functions will use the same template engine.
1. The semantic function has a method called SetAIConfiguration. The parameter type taken by SetAIConfiguration is CompleteRequestSettings. When creating a semantic function. the CompleteRequestSettings are initialized from a CompletionConfig instance.
    1. We have three terms i.e., AIConfiguration, CompleteRequestSettings and CompletionConfig referring to the same thing. We should standardize on one name.
    1. The CompleteRequestSettings /CompletionConfig are very OpenAI specific s it's not possible to define the request settings used by other AI services.
    1. A semantic function has only one CompleteRequestSettings /CompletionConfig instance which means it's not possible to associate model specific settings with a semantic function.
1. Not clear why the PromptTemplateConfig does not contain the template, skill name and function name.
1. The property DefaultServices is only referenced in the method PromptTemplateConfig.Compact(). This method also doesn’t seem to be referenced anywhere and its implementation is questionable because it has a side-effect of changing the instance in order to reduce JSON complexity.

### Proposed Patterns

#### 1. Simple case where semantic function lifecycle matches the semantic kernel and the default template engine is used.

```csharp
IKernel kernel = new KernelBuilder()
    .WithAzureChatCompletionService(deploymentName: modelId, endpoint: endpoint, apiKey: apiKey)
    .Build();

var promptConfig = new PromptConfig()
{
    Template: "Say hello in German",
    Description = "Say hello in German",
    InputParameters = new(),
    skillName: "GermanSkill",
    functionName: "SayHello",
    PromptRequestSettings = new List<PromptRequestSettings>() { … }
};

var function = kernel.CreateSemanticFunction(promptConfig);
```


#### Changes:

The code looks similar to the current pattern but has the following key differences:

1. Introduces the following new classes:
    1. `PromptConfig` - Defines a prompt (aka semantic function) and the capabilities we want a prompt to support.
    2. `PromptRequestSettings` - Defines the request settings used to execute the prompt with a specific model in an AI agnostic fashion.
2. Mark `PromptTemplateConfig` and `SemanticFunctionConfig` as obsolete.
5. Using the new codepath the function does not have a default text completion service associated with it. Instead this is determined when the function is invoked.

#### How to obsolete the current pattern to avoid breaking current clients:

The new code uses new abstractions so the plan would be to make the current methods as obsolete and recommend switching to the new pattern.

### 2. Using PromptRequestSettings when creating a semantic function.

```csharp
var promptRequestSettings = new PromptRequestSettings();
promptRequestSettings.Properties["temperature"] = 0.9;
promptRequestSettings.Properties["max_tokens"] = 1024;

var promptConfig = new PromptConfig()
{
    Description = "Say hello in German",
    InputParameters = new(),
    SkillName = "GermanSkill",
    FunctionName = "SayHello",
    Template = "Say hello in German",
    PromptRequestSettings = new List<PromptRequestSettings>() { promptRequestSettings },
};

IKernel kernel = Kernel.Builder
    .WithAzureTextCompletionService(deploymentName: modelId, endpoint: endpoint, apiKey: apiKey)
    .Build();

var function = kernel.CreateSemanticFunction(promptConfig);

var response = await kernel.RunAsync(function);
```

#### Changes:

1. The `CompleteRequestSettings` gets a new method to create an instance of itself from `PromptConfig.Properties` by using JSON deserialization.
2. In the near future `CompleteRequestSettings` should be moved to the OpenAI connector as it is an OpenAI specific class.
