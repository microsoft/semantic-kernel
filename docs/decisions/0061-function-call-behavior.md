---
# These are optional elements. Feel free to remove any of them.
status: accepted
contact: sergeymenshykh
date: 2024-04-22
deciders: markwallace, matthewbolanos, rbarreto, dmytrostruk, westey-m
consulted: 
informed:
---

# Function Call Behavior

## Context and Problem Statement

Currently, every AI connector in SK that supports function calling has its own implementation of tool call behavior model classes. 
These classes are used to configure how connectors advertise and invoke functions. 
For instance, the behavior classes can specify which functions should be advertised to the AI model by a connector, whether the functions 
should be called automatically by the connector, or if the connector caller will invoke them manually.

All the tool call behavior classes are the same in terms of describing the desired function call behavior. 
However, the classes have a mapping functionality that maps the function call behavior to the connector-specific model classes, 
which is what makes the function calling classes non-reusable between connectors. For example, 
[the constructor of the ToolCallBehavior class](https://github.com/microsoft/semantic-kernel/blob/aec65771c8c2443db2c832aed167bff566d4ab46/dotnet/src/Connectors/Connectors.OpenAI/ToolCallBehavior.cs#L172) references the 
[OpenAIFunction](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/src/Connectors/Connectors.OpenAI/Core/OpenAIFunction.cs) class, which is located in the 
`Microsoft.SemanticKernel.Connectors.OpenAI` namespace within the `Connectors.OpenAI` project.
As a result, these classes cannot be reused by other connectors, such as the Mistral AI connector, without introducing an undesirable explicit project dependency from the `Connectors.Mistral` project to the `Connectors.OpenAI` project.  

Furthermore, it is currently not possible to specify function calling behavior declaratively in YAML or JSON prompts.  

## Decision Drivers
- There should be a single set of connector/model-agnostic function call behavior classes, enabling their use by all SK connectors that support function calling.  
- Function call behavior should be specified in the `PromptExecutionSettings` base class, rather than in its connector-specific derivatives.  
- It should be possible and straightforward to define function calling behavior in all currently supported prompt formats, including YAML (Handlebars, Prompty) and JSON (SK config.json).  
- Users should have the ability to override the prompt execution settings specified in the prompt with those defined in the code.

## Existing function calling behavior model - ToolCallBehavior
Today, SK utilizes the `ToolCallBehavior` abstract class along with its derivatives: `KernelFunctions`, `EnabledFunctions`, and `RequiredFunction` to define the function-calling behavior for the OpenAI connector.
This behavior is specified through the `OpenAIPromptExecutionSettings.ToolCallBehavior` property. The model is consistent across other connectors, differing only in the names of the function call behavior classes.  

```csharp
OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

or

GeminiPromptExecutionSettings settings = new() { ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions };
```

Considering that the function-calling behavior has been in place since the SK v1 release and may be used extensively, the new function-calling abstraction must be introduced to coexist alongside the existing function-calling model. This approach will prevent breaking changes and allow consumers to gradually transition from the current model to the new one.

## [New model] Option 1.1 - A class per function choice
To meet the "no breaking changes" requirement and the "connector/model-agnostic" design principle, a new set of connector-agnostic classes needs to be introduced.

### Function choice classes 
The `FunctionChoiceBehavior` class is abstract base class for all *FunctionChoiceBehavior derivatives.

```csharp
public abstract class FunctionChoiceBehavior
{
    public static FunctionChoiceBehavior Auto(IEnumerable<KernelFunction>? functions = null, bool autoInvoke = true, FunctionChoiceBehaviorOptions? options = null) { ... }
    public static FunctionChoiceBehavior Required(IEnumerable<KernelFunction>? functions = null, bool autoInvoke = true, FunctionChoiceBehaviorOptions? options = null) { ... }
    public static FunctionChoiceBehavior None(IEnumerable<KernelFunction>? functions = null, FunctionChoiceBehaviorOptions? options = null)

    public abstract FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorConfigurationContext context);
}
```

All derivatives of the `FunctionChoiceBehavior` class must implement the abstract `GetConfiguration` method. This method is called with a `FunctionChoiceBehaviorConfigurationContext` provided by the connectors. It returns a `FunctionChoiceBehaviorConfiguration` object to the connectors, instructing them on how to behave based on the specific function call choice behavior defined by the corresponding class regarding function calling and invocation.  


```csharp
public class FunctionChoiceBehaviorConfigurationContext
{
    public Kernel? Kernel { get; init; }
    public ChatHistory ChatHistory { get; }
    public int RequestSequenceIndex { get; init; }
}

public class FunctionChoiceBehaviorConfiguration
{
    public FunctionChoice Choice { get; internal init; }
    public IReadOnlyList<KernelFunction>? Functions { get; internal init; }
    public bool AutoInvoke { get; set; } = true;
    public FunctionChoiceBehaviorOptions Options { get; }
}
```

The `AutoFunctionChoiceBehavior` class can advertise either all kernel functions or a specified subset of functions, which can be defined through its constructor or the `Functions` property. Additionally, it instructs the AI model on whether to call the functions and, if so, which specific functions to invoke.  
```csharp
public sealed class AutoFunctionChoiceBehavior : FunctionChoiceBehavior
{
    [JsonConstructor]
    public AutoFunctionChoiceBehavior() { }
    public AutoFunctionChoiceBehavior(IEnumerable<KernelFunction>? functions, bool autoInvoke, FunctionChoiceBehaviorOptions? options) { }

    [JsonPropertyName("functions")]
    public IList<string>? Functions { get; set; }

    [JsonPropertyName("options")]
    public FunctionChoiceBehaviorOptions? Options { get; set; }

    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorConfigurationContext context)
    {
        var functions = base.GetFunctions(this.Functions, context.Kernel, this._autoInvoke);

        return new FunctionChoiceBehaviorConfiguration(this.Options ?? DefaultOptions)
        {
            Choice = FunctionChoice.Auto,
            Functions = functions,
            AutoInvoke = this._autoInvoke,
        };
    }
}
```
   
The `RequiredFunctionChoiceBehavior` class, like the `AutoFunctionChoiceBehavior` class, can advertise either all kernel functions or a specified subset of functions, which can be defined through its constructor or the `Functions` property. However, it differs by mandating that the model must call the provided functions.  
```csharp
public sealed class RequiredFunctionChoiceBehavior : FunctionChoiceBehavior
{
    [JsonConstructor]
    public RequiredFunctionChoiceBehavior() { }
    public RequiredFunctionChoiceBehavior(IEnumerable<KernelFunction>? functions, bool autoInvoke, FunctionChoiceBehaviorOptions? options) { }

    [JsonPropertyName("functions")]
    public IList<string>? Functions { get; set; }

    [JsonPropertyName("options")]
    public FunctionChoiceBehaviorOptions? Options { get; set; }

    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorConfigurationContext context)
    {
        // Stop advertising functions after the first request to prevent the AI model from repeatedly calling the same function.
        // This is a temporary solution which will be removed after we have a way to dynamically control list of functions to advertise to the model.
        if (context.RequestSequenceIndex >= 1)
        {
            return new FunctionChoiceBehaviorConfiguration(this.Options ?? DefaultOptions)
            {
                Choice = FunctionChoice.Required,
                Functions = null,
                AutoInvoke = this._autoInvoke,
            };
        }

        var functions = base.GetFunctions(this.Functions, context.Kernel, this._autoInvoke);

        return new FunctionChoiceBehaviorConfiguration(this.Options ?? DefaultOptions)
        {
            Choice = FunctionChoice.Required,
            Functions = functions,
            AutoInvoke = this._autoInvoke,
        };
    }
}
```

The `NoneFunctionChoiceBehavior` class, like the other behavior classes, can advertise either all kernel functions or a specified subset of functions, which can be defined through its constructor or the `Functions` property. Additionally, it instructs the AI model to utilize the provided functions without calling them to generate a response. This behavior may be useful for dry runs when you want to see which functions the model would call without actually invoking them.  
```csharp
public sealed class NoneFunctionChoiceBehavior : FunctionChoiceBehavior
{
    [JsonConstructor]
    public NoneFunctionChoiceBehavior() { }
    public NoneFunctionChoiceBehavior(IEnumerable<KernelFunction>? functions, FunctionChoiceBehaviorOptions? options) { }

    [JsonPropertyName("functions")]
    public IList<string>? Functions { get; set; }

    [JsonPropertyName("options")]
    public FunctionChoiceBehaviorOptions? Options { get; set; }

    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorConfigurationContext context)
    {
        var functions = base.GetFunctions(this.Functions, context.Kernel, autoInvoke: false);

        return new FunctionChoiceBehaviorConfiguration(this.Options ?? DefaultOptions)
        {
            Choice = FunctionChoice.None,
            Functions = functions,
            AutoInvoke = false,
        };
    }
}
```

To meet the requirements of the 'connector/model-agnostic' driver, the function choice behavior should be configurable within the model-agnostic `PromptExecutionSettings` class, rather than within the model-specific prompt execution setting classes, such as `OpenAIPromptExecutionSettings`, as is currently done.

```csharp
PromptExecutionSettings settings = new() { FunctionChoiceBehavior = FunctionChoiceBehavior.Required() };
```
   
All of the function choice behavior classes described above include a `Functions` property of type `IList<string>`.
Functions can be specified as strings in the format `pluginName.functionName`. The primary purpose of this property is to allow users to declare the list of functions they wish to advertise to 
the AI model in YAML, Markdown, or JSON prompts. However, it can also be utilized to specify the functions in code, although it is generally more convenient to do this through 
the constructors of the function choice behavior classes, which accept a list of `KernelFunction` instances.  
   
Additionally, the function choice behavior classes feature an `Options` property of type `FunctionChoiceBehaviorOptions`, which can be provided via the constructor or set directly on the class instance.
This property enables users to configure various aspects of the function choice behavior, such as whether the AI model should prefer parallel function invocations over sequential ones. 
The intention is for this class to evolve over time, incorporating properties that are relevant to the majority of AI models. 
In cases where a specific AI model requires unique properties that are not supported by other models, a model-specific derivative options class can be created.
This class can be recognized by the SK AI connector for that model, allowing it to read the specific properties.

### Sequence diagram
<img src="./diagrams/tool-behavior-usage-by-ai-service.png" alt="Tool choice behavior usage by AI service.png" width="600"/>

### Support of the behaviors in prompts
Given the hierarchical nature of the choice behavior model classes, polymorphic deserialization should be enabled for situations where functional choice behavior needs to be configured in JSON and YAML prompts.
```json
{
    ...
    "execution_settings": {
        "default": {
            "temperature": 0.4,
            "function_choice_behavior": {
                "type": "auto", //possible values - auto, required, none
                "functions": [
                    "plugin1.function1",
                    "plugin1.function2",
                ],
                "options": {
                    "allow_concurrent_invocation": true
                }
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
      functions:
      - plugin1.function1
      - plugin1.function2
      options:
        allow_concurrent_invocation: true
```
Polymorphic deserialization is supported by System.Text.Json.JsonSerializer and requires registering all the types that will be used for polymorphic deserialization, in advance, before they can be used.
This can be done either by annotating the base class with the JsonDerivedType attribute to specify a subtype of the base type, or alternatively, by registering the subtypes in TypeInfoResolver, 
which needs to be supplied via JsonSerializerOptions for use during deserialization. 
More details can be found here: [Serialize polymorphic types](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/polymorphism?pivots=dotnet-8-0).

To support custom function choice behaviors, the custom types should be registered for polymorphic deserialization. 
Clearly, the approach using the JsonDerivedType attribute is not viable, as users cannot annotate `FunctionChoiceBehavior` SK class. 
However, they could register their custom type resolver that would register their custom type(s) if they had access to JsonSerializerOptions used by JsonSerializer during deserialization. 
Unfortunately, SK does not expose those options publicly today. Even if it had, there are YAML prompts that are deserialized by the YamlDotNet library that would require same custom types supplied via YAML specific deserializer extensibility mechanisms - YamlTypeConverter. 
This would mean that if a user wants the same custom function calling choice to be used in both YAML and JSON prompts, they would have to register the same custom type twice - for JSON 
via a custom type resolver and for YAML via a custom YamlTypeConverter. That would also require a mechanism of supplying custom resolvers/converters to all SK `CreateFunctionFrom*Prompt` extension methods.


Polymorphic deserialization is supported by `System.Text.Json.JsonSerializer` and requires that all types intended for polymorphic deserialization be registered in advance. 
This can be accomplished either by annotating the base class with the `JsonDerivedType` attribute to specify a subtype of the base type or by registering the subtypes with `TypeInfoResolver`, 
which must be provided via `JsonSerializerOptions` for use during deserialization. 
More details can be found here: [Serialize polymorphic types](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/polymorphism?pivots=dotnet-8-0).  

### Location of the function choice behavior node
SK prompts may contain one or more entries, each corresponding to a service, which specify execution settings to describe service-specific configurations within a prompt. 
Since each section is deserialized into an instance of the `PromptExecutionSettings` class, which is utilized by the respective service, 
it is logical to define the function behavior in each service configuration section.
However, this approach may lead to unnecessary duplication, as all services might require the same choice behavior. 
Furthermore, there may be scenarios where two out of three services share the same choice behavior configuration, while the remaining service uses a different one.

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
To address the scenarios mentioned above, it is advisable to implement an inheritance mechanism that allows a service to inherit the parent function choice behavior configuration, if specified. 
Regardless of whether the parent has a function choice behavior configuration defined, it should be possible to specify or override the parent's configuration at each service entry level.

### Breaking glass support
The list of choice classes described above may not be sufficient to cover all scenarios that users might encounter. 
To address this, the `FunctionCallChoice.Configure` method accepts an instance of the model connector used internally, enabling users to access and modify it from within the configuration method of a custom function call choice.
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

## [New model] Option 1.2 - alternative design
Explore the possibility of resolving specific types during a post-deserialization phase in a location that has access to a kernel instance, eliminating the need for polymorphic deserialization. 
This approach would enable the resolution of custom function choice behavior classes that users register in the kernel service collection. Users can register their custom classes, which will then be automatically selected either during prompt rendering or when the information is needed, regardless of the prompt format whether it's JSON or YAML.  

## 2. Separation of function call choice and function invocation configs
The new model should accommodate scenarios where one person engineers the prompt while another executes or invokes it. 
One way to achieve this is by separating function choice behavior configuration such as auto, enabled, and none from function invocation configuration, which includes settings like AllowParallelCalls. 
The function choice behavior configuration can still be provided through PromptExecutionSettings, but the appropriate location for supplying the function invocation configuration needs to be identified. 
Additionally, it should be possible to override function choice behavior directly from the code. Below are several options for potential locations to supply function invocation configuration via the code:

### Option 2.1 - Invocation config as a parameter of the `IChatCompletionService.GetChatMessageContentsAsync` method and its streaming counterpart.
Pros:  
- The function invocation configuration can be specified for each operation, rather than being limited to the overall AI service configuration.
   
Cons:  
- Introducing a new parameter to the interface methods will create breaking changes that will impact all non-SK custom implementations of the interface.
- This approach diverges from the current development experience, which allows both configurations to be supplied through connector-specific prompt execution settings.

### Option 2.2 - Invocation config as a constructor parameter of each implementation of the `IChatCompletionService` interface.
Pros:  
- There is no need to change the interface method signatures, which means that no non-SK custom implementations will be broken.
   
Cons:  
- The function invocation configuration will be applied at the service level during the service registration phase. If some operations require different configurations, a new service with a distinct configuration will need to be registered.
- This approach diverges from the current development experience, where both configurations are provided through connector-specific prompt execution settings.

### Option 2.3 - Invocation config as `Kernel.FunctionInvocationConfig` property.
Pros:
- No breaking changes: The signatures of both `IChatCompletionService` members and its implementation constructors remain unchanged.

Cons:
- A new kernel must be created, or an existing one must be cloned, each time a different configuration is required.
- The kernel will contain more AI connector-specific logic.
- This approach deviates from the current development experience, where both configurations are provided through connector-specific prompt execution settings.

### Option 2.4 - Invocation config as item in `Kernel.Data` collection.
Pros:  
- No breaking changes: The signatures of both `IChatCompletionService` members and its implementation constructors remain unchanged.
- No AI connector-specific logic is added to the kernel.
   
Cons:  
- Requires a magic constant that is not enforced by the compiler.
- A new kernel must be created, or an existing one must be cloned, each time a different configuration is needed.
- This approach deviates from the current development experience, where both configurations are provided through connector-specific prompt execution settings.

### Option 2.5 - The `PromptExecutionSettings.FunctionChoiceBehavior` property for both function call choice config and invocation config
Pros:
- This approach is proposed in Option #1.1, where both configurations are supplied through connector-agnostic prompt execution settings.
- No breaking changes: The signatures of both `IChatCompletionService` members and its implementation constructors remain unchanged.

Cons:
- A new service selector must be implemented and registered in the kernel to merge execution settings provided via the prompt with those supplied by developers at the invocation step

## Decision Outcome
There were a few decisions taken during the ADR review:
- Option 1.1 was chosen as the preferred option for the new function call behavior model.
- It was decided to postpone the implementation of the inheritance mechanism that allows a service to inherit the parent function choice behavior configuration.
- It was decided that the Breaking Glass support is out of scope for now, but it may be included later if necessary.
- Option 2.5, which presumes supplying function call choices and function invocation configurations via prompt execution settings, was preferred over the other options due to its simplicity, absence of breaking changes, and familiar developer experience.
