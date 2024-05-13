---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: sergeymenshykh
date: 2024-04-22
deciders: markwallace, matthewbolanos, rbarreto, dmytrostruk, westey-m
consulted: 
informed:
---

# Function Call Behavior

## Context and Problem Statement

Today, every AI connector in SK that supports function calling has its own implementation of tool call behavior model classes. These classes are used to configure the way connectors advertise and invoke functions. For example, the behavior classes can describe which functions should be advertised to LLM by a connector, whether the functions should be called automatically by the connector, or if the connector caller will invoke them himself manually, etc.  
   
All the tool call behavior classes are the same in terms of describing the desired function call behavior. However, the classes have a mapping functionality to map the function call behavior to the connector-specific model classes, and that's what makes the function calling classes non-reusable between connectors. For example, [the constructor of the ToolCallBehavior class](https://github.com/microsoft/semantic-kernel/blob/0c40031eb917bbf46c9af97897051f45e4084986/dotnet/src/Connectors/Connectors.OpenAI/ToolCallBehavior.cs#L165) references the [OpenAIFunction](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Connectors/Connectors.OpenAI/AzureSdk/OpenAIFunction.cs) class that lives in the `Microsoft.SemanticKernel.Connectors.OpenAI` namespace declared in the `Connectors.OpenAI` project. The classes can't be reused by, let's say, the Mistral AI connector without introducing an explicit project dependency from the `Connectors.Mistral` project to the `Connectors.OpenAI` project, a dependency we definitely don't want to have.

Additionally, today, it's not possible to specify function calling behavior declaratively in YAML, MD, and Kernel(config.json) prompts.

## Decision Drivers

- The same set of function call behavior model classes should be connector/mode-agnostic, allowing them to be used by all SK connectors that support function calling.
- Function calling behavior should be specified in the `PromptExecutionSettings` base class rather than in connector-specific derivatives.
- It should be possible and easy to specify function calling behavior in all already supported YAML, MD, and SK(config.json) prompts.
- It should be possible to override the prompt execution settings specified in the prompt by using the prompt execution settings specified in the code.

## Existing function calling behavior model - ToolCallBehavior
Today, SK uses the `ToolCallBehavior` abstract class and its derivatives `KernelFunctions`, `EnabledFunctions`, and `RequiredFunction` to define function calling behavior for the OpenAI connector. The behavior is specified via the `OpenAIPromptExecutionSettings.ToolCallBehavior` property. The model is identical for other connectors and differs only in the function call behavior class names.

```csharp
OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

or

GeminiPromptExecutionSettings settings = new() { ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions };
```

Taking into account that the function-calling behavior has been around since SK v1 release and might be used extensively as a result, the new function-calling abstraction must be introduced and coexist alongside the existing function-calling model. This will prevent breaking changes and allow consumers to gradually migrate from the current model to the new one.

## [New model] Option 1.1 - A class per function call choice
To satisfy the "no breaking changes" requirement above and the "connector/mode-agnostic model" decision driver, the new set of connector agnostic classes needs to be introduced.

### Function call choice classes 
The `FunctionChoiceBehavior` class is abstract base class for all *FunctionChoiceBehavior classes:

```csharp
public abstract class FunctionChoiceBehavior
{
    public static FunctionChoiceBehavior AutoFunctionChoice(IEnumerable<KernelFunction>? functions = null, bool autoInvoke = true) { ... }
    public static FunctionChoiceBehavior RequiredFunctionChoice(IEnumerable<KernelFunction>? functions = null, bool autoInvoke = true) { ... }
    public static FunctionChoiceBehavior None { get { ... }; }

    public abstract FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context);
}
```

All the `FunctionChoiceBehavior` derivatives must implement the abstract `GetConfiguration` method, which is called with the `FunctionChoiceBehaviorContext` provided by connectors. This method returns the `FunctionChoiceBehaviorConfiguration` back to the connectors, instructing them to behave in a specific way described by a particular function call choice behavior class with respect to function calling.

```csharp
public class FunctionChoiceBehaviorContext
{
    public Kernel? Kernel { get; init; }
}

public class FunctionCallChoiceConfiguration
{
    public IEnumerable<KernelFunctionMetadata>? AvailableFunctions { get; init; }
    public IEnumerable<KernelFunctionMetadata>? RequiredFunctions { get; init; }
    public bool? AllowAnyRequestedKernelFunction { get; init; }
    public int? MaximumAutoInvokeAttempts { get; init; }
    public int? MaximumUseAttempts { get; init; }
}
```

The `AutoFunctionChoiceBehavior` class advertises either all kernel functions or a subset of functions, and instructs LLM to either call one or multiple advertised functions or return a natural language response.
```csharp
public sealed class AutoFunctionChoiceBehavior : FunctionChoiceBehavior
{
    private const int DefaultMaximumAutoInvokeAttempts = 5;

    [JsonConstructor]
    public AutoFunctionChoiceBehavior() { }
    public AutoFunctionChoiceBehavior(IEnumerable<KernelFunction> functions) { ... }

    [JsonPropertyName("maximumAutoInvokeAttempts")]
    public int MaximumAutoInvokeAttempts { get; init; } = DefaultMaximumAutoInvokeAttempts;

    [JsonPropertyName("functions")]
    public IEnumerable<string>? Functions { get; init; }

    [JsonPropertyName("allowAnyRequestedKernelFunction")]
    public bool AllowAnyRequestedKernelFunction { get; init; }

    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context)
    {
        // Handle functions provided via constructor as function instances.
        ...
        // Or, handle functions provided via the 'Functions' property as function fully qualified names.
        ...
        // Or, provide all functions from the kernel.

        return new FunctionChoiceBehaviorConfiguration()
        {
            AvailableFunctions = availableFunctions,
            MaximumAutoInvokeAttempts = this.MaximumAutoInvokeAttempts,
            AllowAnyRequestedKernelFunction = this.AllowAnyRequestedKernelFunction
        };
    }
}
```

The `RequiredFunctionChoiceBehavior` class advertises either all kernel functions or a subset of functions and forces LLM to call one or a few of them.
```csharp
public sealed class RequiredFunctionChoiceBehavior : FunctionChoiceBehavior
{
    private const int DefaultMaximumAutoInvokeAttempts = 5;
    private const int DefaultMaximumUseAttempts = 1;

    [JsonConstructor]
    public RequiredFunctionChoiceBehavior() { }
    public RequiredFunctionChoiceBehavior(IEnumerable<KernelFunction> functions) { ... }

    [JsonPropertyName("functions")]
    public IEnumerable<string>? Functions { get; init; }

    [JsonPropertyName("maximumAutoInvokeAttempts")]
    public int MaximumAutoInvokeAttempts { get; init; } = DefaultMaximumAutoInvokeAttempts;

    [JsonPropertyName("maximumUseAttempts")]
    public int MaximumUseAttempts { get; init; } = DefaultMaximumUseAttempts;

    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context)
    {
        // Handle functions provided via constructor as function instances.
        ...
        // Or, handle functions provided via the 'Functions' property as function fully qualified names.
        ...
        // Or, provide all functions from the kernel.

        return new FunctionCallChoiceConfiguration()
        {
            RequiredFunctions = requiredFunctions,
            MaximumAutoInvokeAttempts = this.MaximumAutoInvokeAttempts,
            MaximumUseAttempts = this.MaximumUseAttempts,
            AllowAnyRequestedKernelFunction = allowAnyRequestedKernelFunction
        };
    }
}
```

The `NoneFunctionChoiceBehavior` class instructs the model not to call functions.
```csharp
public sealed class NoneFunctionChoiceBehavior : FunctionChoiceBehavior
{
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context)
    {
        return new FunctionChoiceBehaviorConfiguration()
        {
            AvailableFunctions = null,
            RequiredFunctions = null,
        };
    }
}
```

To satisfy the "connector/mode-agnostic model" driver, the behavior should not be configured on model-specific prompt execution setting classes, such as `OpenAIPromptExecutionSettings`, as it is done today. Instead, it should be configured on a model-agnostic one - `PromptExecutionSettings`.

```csharp
PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.RequiredFunctionChoice() };
```

### Sequence diagram
<img src="./diagrams/tool-behavior-usage-by-ai-service.png" alt="Tool choice behavior usage by AI service.png" width="600"/>

### [Out of scope]Breaking glass support
The list of choice classes described above may not be sufficient to support all scenarios users might encounter. To accommodate these, the `FunctionCallChoice.Configure` method accepts an instance of model a connector use internally, allowing users to access and modify it from within the config method of a custom function call choice.
```csharp
// Custom function call choice
public sealed class NewCustomFunctionChoiceBehavior : FunctionChoiceBehavior
{
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context)
    {
        var model = context.Model;

        // The CompletionsOptions, ChatCompletionsToolChoice, etc are data model classes used by the OpenAIChatCompletionService connector internally.
        ((CompletionsOptions)model).ToolChoice = new ChatCompletionsToolChoice(new FunctionDefinition("NEW-TOOL-CHOICE-MODE"));
        ((CompletionsOptions)model).Tools.Add(new ChatCompletionsFunctionToolDefinition(<functions-to-advertise>);
 
        return new FunctionChoiceBehaviorConfiguration()
        {
            Model = model; // Return the model back to the calling connector to indicate that we control the function call choice ourselves, and there is no need to apply the mapping logic connector side that would be applied otherwise.
            MaximumAutoInvokeAttempts = this.MaximumAutoInvokeAttempts,
            MaximumUseAttempts = this.MaximumUseAttempts,
            AllowAnyRequestedKernelFunction = false
        };
    }
}
...

// Registering the custom choice
PromptExecutionSettings settings = new() { FunctionChoiceBehavior = new NewCustomFunctionChoiceBehavior() };
```

### Support in JSON prompts
Considering the hierarchical nature of the choice behavior model classes, polymorphic deserialization should be enabled for instances when functional choice behavior needs to be configured in JSON prompts - MD and Kernel (config.json) prompts, as well as YAML prompts - handlebars.
```json
{
    ...
    "execution_settings": {
        "default": {
            "temperature": 0.4,
            "function_choice_behavior": {
                "type": "auto", //possible values - auto, required, none
                "functions": [
                    "plugin1.function1"
                ],
                "maximumAutoInvokeAttempts": 5,
            }
        }
    }
}
```
```yaml
execution_settings:
  default:
    temperature: 0.4
    function_choice_behavior:
      type: auto
      maximum_auto_invoke_attempts: 5
      functions:
      - plugin1.function1
```
Polymorphic deserialization is supported by System.Text.Json.JsonSerializer, which SK uses for working with JSON content. The JsonSerializer requires registering all the types that will be used for polymorphic deserialization. This can be done either by annotating the base class with the JsonDerivedType attribute to specify a subtype of the base type, or alternatively, by registering the subtypes in TypeInfoResolver, which needs to be supplied via JsonSerializerOptions for use during deserialization. More details can be found here: [Serialize polymorphic types](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/polymorphism?pivots=dotnet-8-0).

To support custom function choice behaviors, the custom types should be registered for polymorphic deserialization. Clearly, the approach using the JsonDerivedType attribute is not viable, as users cannot annotate `FunctionChoiceBehavior` SK class. However, they could register their custom type resolver that would register their custom type(s) if they had access to JsonSerializerOptions used by JsonSerializer during deserialization. Unfortunately, SK does not expose those options publicly today. Even if it had, there are YAML prompts that are deserialized by the YamlDotNet library that would require same custom types supplied via YAML specific deserializer extensibility mechanisms - YamlTypeConverter. This would mean that if a user wants the same custom function calling choice to be used in both YAML and JSON prompts, they would have to register the same custom type twice - for JSON via a custom type resolver and for YAML via a custom YamlTypeConverter. That would also require a mechanism of supplying custom resolvers/converters to all SK `CreateFunctionFrom*Prompt` extension methods.

### Location of the function choice behavior node
SK prompts may have one or more entries, one per service, of execution settings to describe service-specific configurations in a prompt. Considering that each section is deserialized to an instance of the `PromptExecutionSettings` class and that class is used by the corresponding service, it makes sense to specify the function behavior in each service configuration section. On the other hand, this may introduce unnecessary duplication because all services might need exactly the same choice behavior. Additionally, there could be scenarios where 2 out of 3 services use the same choice behavior configuration, while the remaining one uses a different one.
```json
"function_choice_behavior":{
    ...
},
"execution_settings": {
   "default": {
     "temperature": 0,
     "function_choice_behavior":{
        ...
     }
   },
   "gpt-3.5-turbo": {
     "model_id": "gpt-3.5-turbo-0613",
     "temperature": 0.1,
     "function_choice_behavior":{
        ...
     }
   },
   "gpt-4": {
     "model_id": "gpt-4-1106-preview",
     "temperature": 0.3,
     "function_choice_behavior":{
        ...
     }
   }
 }
```
To accommodate the scenarios above, it makes sense to introduce an inheritance mechanism that would inherit the parent function choice behavior configuration, if specified. Regardless of whether the parent has a function choice behavior configuration specified or not, it should be possible to specify or override the parent's configuration at each service entry level.

## [New model] Option 1.2 - alternative design
Explore the possibility of resolving specific types at a later post-deserialization phase and in a location with access to a kernel instance, so no polymorphic deserialization would be required. This would allow for the resolution of custom classes registered by users in the kernel service collection. Users will simply register the custom classes that will be automatically picked either during prompt rendering or at the moment the information is required, regardless of the prompt format - JSON or YAML.

## 2. Separation of function call choice and function invocation configs
The new model should support scenarios in which the prompt is engineered by one person and executed or invoked by another. One way to achieve this is to separate function  choice behavior configuration - auto, enabled, none - from function invocation configuration, such as MaximumAutoInvokeAttempts, InvokeInParallel, etc. The function choice behavior configuration can still be provided through PromptExecutionSettings, while the appropriate location for supplying the function invocation configuration needs to be identified. It should be possible to override function choice behavior from the code as well. Below are several options considering potential places for supplying function invocation configuration via the code:

### Option 2.1 - Supplying function invocation config as a parameter of the `IChatCompletionService.GetChatMessageContentsAsync` and `IChatCompletionService.GetStreamingChatMessageContentsAsync` methods.
Pros:  
- The function invocation configuration can be supplied per operation, rather than per AI service configuration.  
   
Cons:  
- Adding a new parameter to the interface methods will introduce breaking changes that will affect all non-SK custom implementations of the interface.  
- This approach deviates from the current development experience, where both configurations are supplied via connector-specific prompt execution settings.

### Option 2.2 - Supplying function invocation config as a constructor parameter of each implementation of the `IChatCompletionService` interface.
Pros:  
- No need to change the interface method signatures - so no non-SK custom implementations will be broken.  
   
Cons:  
- The function invocation configuration will be applied at the service level during the service registration phase. If some operations need different configurations, a new service with a different config needs to be registered.  
- This approach will require adding overloaded constructors for all AI SK services/connectors. This may potentially cause the "ambiguous constructor" problem that may require an additional solution.  
- This approach deviates from the current development experience, where both configurations are supplied via connector-specific prompt execution settings.

### Option 2.3 - Supplying function invocation config via a new `Kernel.FunctionInvocationConfig` property.
Pros:
- No breaking changes - neither `IChatCompletionService` members signatures nor its implementation constructors signatures are changed.

Cons:
- A new kernel needs to be created or existing one needs to be cloned every time a different configuration is required.
- Kernel gets more AI connector specific logic.
- This approach deviates from the current development experience, where both configurations are supplied via connector-specific prompt execution settings.

### Option 2.4 - Supplying function invocation config via `Kernel.Data` collection.
Pros:  
- No breaking changes - neither `IChatCompletionService` member signatures nor its implementation constructor signatures are changed.  
- No AI connector-specific logic is added to the Kernel.  
   
Cons:  
- Requires a magic constant that is not enforced by the compiler.  
- A new kernel needs to be created or an existing one needs to be cloned every time a different configuration is required.  
- This approach deviates from the current development experience, where both configurations are supplied via connector-specific prompt execution settings.

### Option 2.5 - Existing approach - supplying function invocation config via `PromptExecutionSettings`.
Pros:
- This is the existing approach, where both configurations are supplied via connector-specific prompt execution settings.
- No breaking changes - neither IChatCompletionService member signatures nor its implementation constructor signatures are changed.

Cons:
- A new service selector needs to be implemented and registered on the Kernel to merge execution settings provided via the prompt with execution settings provided by developers at the invocation step.

## Questions
- Today, the existing tool call behavior can accept and advertise [OpenAI functions](https://github.com/microsoft/semantic-kernel/blob/0296329886eb2116a66e5362f2cc72b42ee30157/dotnet/src/Connectors/Connectors.OpenAI/ToolCallBehavior.cs#L68). These functions are not registered in SK, and SK can only invoke them in 'manual' mode; the 'auto' mode requires the function to be registered on the kernel and throws an exception if that is not the case. Do we have a scenario that requires this functionality?

## Decision Outcome
There were a few decisions taken during the ADR review:
- The Breaking glass support is out of scope. It may be added later if/when needed.
- The `PromptExecution.ToolBehaviors` property should support only one behavior. The original design described in Option 1 supported multiple tool behaviors configured per service. However, it was pointed out that this might not be necessary, could confuse SK users, and adds unnecessary complexity that degrades developer experience.
- Option 2.5, which presumes supplying function call choices and function invocation configurations via prompt execution settings, was preferred over the other options due to its simplicity, absence of breaking changes, and familiar developer experience.
