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

## Existing function calling behavior model - ToolCallBehavior
Today, SK uses the `ToolCallBehavior` abstract class and its derivatives `KernelFunctions`, `EnabledFunctions`, and `RequiredFunction` to define function calling behavior for the OpenAI connector. The behavior is specified via the `OpenAIPromptExecutionSettings.ToolCallBehavior` property. The model is identical for other connectors and differs only in the function call behavior class names.

```csharp
OpenAIPromptExecutionSettings settings = new() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions };

or

GeminiPromptExecutionSettings settings = new() { ToolCallBehavior = GeminiToolCallBehavior.AutoInvokeKernelFunctions };
```

Taking into account that the function-calling behavior has been around since SK v1 release and might be used extensively as a result, the new function-calling abstraction must be introduced and coexist alongside the existing function-calling model. This will prevent breaking changes and allow consumers to gradually migrate from the current model to the new one.

## Option 1
To satisfy the "no breaking changes" requirement above and the "connector/mode-agnostic model" decision driver, the new set of connector agnostic classes needs to be introduced.

### Tool behavior classes
The `ToolBehavior` class is an abstract base class for all existing and new *Behavior classes. The `FunctionCallBehavior` represents the configuration for function call behavior and is currently the only derivative of the `ToolBehavior` class that SK has.

```csharp
public abstract class ToolBehavior
{
}

public class FunctionCallBehavior : ToolBehavior
{
    [JsonPropertyName("choice")]
    public FunctionCallChoice Choice { get; init; } = new NoneFunctionCallChoice();

    [JsonPropertyName("parallel")]
    public bool InvokeInParallel { get; init; } = false;  // Can be added later.

    public static FunctionCallBehavior AutoFunctionChoice(IEnumerable<KernelFunction>? enabledFunctions = null, bool autoInvoke = true) { ... }
    public static FunctionCallBehavior RequiredFunctionChoice(IEnumerable<KernelFunction> functions, bool autoInvoke = true) { ... }
    public static FunctionCallBehavior None { get { ... }; } 
}

// This is an example of how code interpreter tool can be modeled
public class CodeInterpreterBehavior : ToolBehavior
{
    public string Language { get; init; } = "Python"
    // Other code interpreter specific config props
}
```

To satisfy the "connector/mode-agnostic model" driver, the behavior should not be configured on model-specific prompt execution setting classes, such as `OpenAIPromptExecutionSettings`, as it is done today. Instead, it should be configured on a model-agnostic one, like `PromptExecutionSettings`. Considering that new tools may become available in the future, it makes sense to provide the ability to easily support them. This way, later on, it would simply be a matter of adding a new directive of the `ToolBehavior` class and assigning its instance to the `ToolBehavior` property.

```csharp
PromptExecutionSettings settings = new() { ToolBehavior = FunctionCallBehavior.AutoFunctionChoice(autoInvoke: false) };
```

### Function call choice classes 
The `FunctionCallChoice` class is abstract base class for all *FunctionCallChoice classes:

```csharp
public abstract class FunctionCallChoice
{
    public abstract FunctionCallChoiceConfiguration Configure(FunctionCallChoiceContext context);
}
```

All the `FunctionCallChoice` derivatives must implement the abstract `Configure` method, which is called with the `FunctionCallChoiceContext` provided by connectors. This method returns the `FunctionCallChoiceConfiguration` back to the connectors, instructing them to behave in a specific way described by a function call choice with respect to function calling.
```csharp
public class FunctionCallChoiceContext
{
    public Kernel? Kernel { get; init; }
    public object? Model { get; init; } // Internal connector model
}

public class FunctionCallChoiceConfiguration
{
    public IEnumerable<KernelFunctionMetadata>? AvailableFunctions { get; init; }
    public IEnumerable<KernelFunctionMetadata>? RequiredFunctions { get; init; }
    public bool? AllowAnyRequestedKernelFunction { get; init; }
    public int? MaximumAutoInvokeAttempts { get; init; }
    public int? MaximumUseAttempts { get; init; }
    public object? Model { get; init; }
}
```

The `AutoFunctionCallChoice` class advertises either all kernel functions or a subset of functions, and instructs LLM to either call one or multiple advertised functions or return a natural language response.
```csharp
public sealed class AutoFunctionCallChoice : FunctionCallChoice
{
    internal const int DefaultMaximumAutoInvokeAttempts = 5;

    [JsonConstructor]
    public AutoFunctionCallChoice() { }
    public AutoFunctionCallChoice(IEnumerable<KernelFunction> functions) { ... }

    [JsonPropertyName("maximumAutoInvokeAttempts")]
    public int MaximumAutoInvokeAttempts { get; init; } = DefaultMaximumAutoInvokeAttempts;

    [JsonPropertyName("functions")]
    public IEnumerable<string>? Functions { get; init; }

    [JsonPropertyName("allowAnyRequestedKernelFunction")]
    public bool AllowAnyRequestedKernelFunction { get; init; }

    public override FunctionCallChoiceConfiguration Configure(FunctionCallChoiceContext context)
    {
        ...

        return new FunctionCallChoiceConfiguration()
        {
            AvailableFunctions = availableFunctions,
            MaximumAutoInvokeAttempts = this.MaximumAutoInvokeAttempts,
            AllowAnyRequestedKernelFunction = this.AllowAnyRequestedKernelFunction
        };
    }
}
```

The `RequiredFunctionCallChoice` class advertises subset of kernel functions and forces LLM to call one or a few of them.
```csharp
public sealed class RequiredFunctionCallChoice : FunctionCallChoice
{
    internal const int DefaultMaximumAutoInvokeAttempts = 5;
    internal const int DefaultMaximumUseAttempts = 1;

    [JsonConstructor]
    public RequiredFunctionCallChoice() { }
    public RequiredFunctionCallChoice(IEnumerable<KernelFunction> functions) { ... }

    [JsonPropertyName("functions")]
    public IEnumerable<string>? Functions { get; init; }

    [JsonPropertyName("maximumAutoInvokeAttempts")]
    public int MaximumAutoInvokeAttempts { get; init; } = DefaultMaximumAutoInvokeAttempts;

    [JsonPropertyName("maximumUseAttempts")]
    public int MaximumUseAttempts { get; init; } = DefaultMaximumUseAttempts;

    public override FunctionCallChoiceConfiguration Configure(FunctionCallChoiceContext context)
    {
        ...

        return new FunctionCallChoiceConfiguration()
        {
            RequiredFunctions = requiredFunctions,
            MaximumAutoInvokeAttempts = this.MaximumAutoInvokeAttempts,
            MaximumUseAttempts = this.MaximumUseAttempts,
            AllowAnyRequestedKernelFunction = false
        };
    }
}
```

The `NoneFunctionCallChoice` class instructs the model not to call functions.
```csharp
public sealed class NoneFunctionCallChoice : FunctionCallChoice
{
    public override FunctionCallChoiceConfiguration Configure(FunctionCallChoiceContext context)
    {
        return new FunctionCallChoiceConfiguration()
        {
            MaximumAutoInvokeAttempts = 0,
            MaximumUseAttempts = 0,
            AllowAnyRequestedKernelFunction = false
        };
    }
}
```
### Sequence diagram
<img src="./diagrams/tool-behavior-usage-by-ai-service.png" alt="Tool behavior usage by AI service.png" width="600"/>

### Breaking glass support
The list of choice classes described above may not be sufficient to support all scenarios users might encounter. To accommodate these, the `FunctionCallChoice.Configure` method accepts an instance of model a connector use internally, allowing users to access and modify it from within the config method of a custom function call choice.
```csharp
// Custom function call choice
public sealed class NewCustomFunctionCallChoice : FunctionCallChoice
{
    public override FunctionCallChoiceConfiguration Configure(FunctionCallChoiceContext context)
    {
        var model = context.Model;

        // The CompletionsOptions, ChatCompletionsToolChoice, etc are data model classes used by the OpenAIChatCompletionService connector internally.
        ((CompletionsOptions)model).ToolChoice = new ChatCompletionsToolChoice(new FunctionDefinition("NEW-TOOL-CHOICE-MODE"));
        ((CompletionsOptions)model).Tools.Add(new ChatCompletionsFunctionToolDefinition(<functions-to-advertise>);
 
        return new FunctionCallChoiceConfiguration()
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
PromptExecutionSettings settings = new() { ToolBehavior = new FunctionCallBehavior { Choice = new NewCustomFunctionCallChoice() } };
```

### Support in JSON prompts
Taking into account the hierarchical nature of the behavior and choice model classes described above, polymorphic deserialization should be enabled for cases when tool behavior and function-calling choices need to be configured in JSON prompts like MD and Kernel (config.json) prompts. The same applies to YAML prompts like handlebars described in the next section.
```json
{
    ...
    "execution_settings": {
        "default": {
            "temperature": 0.4,
            "tool_behavior": {
                "type": "functions_call_behavior",
                "choice":{
                    "type": "auto",
                    "functions":[
                        "plugin1.function1"
                    ]
                }
            }
        }
    }
}
```
Polymorphic deserialization is supported by System.Text.Json.JsonSerializer, which SK uses for working with JSON content. The JsonSerializer requires registering all the types that will be used during deserialization. This can be done either by annotating the base class with the JsonDerivedType attribute to specify a subtype of the base type, or alternatively, by registering the subtypes in TypeInfoResolver, which needs to be supplied via JsonSerializerOptions for use during deserialization. More details can be found here: [Serialize polymorphic types](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/polymorphism?pivots=dotnet-8-0).

To support custom tool behaviors or function call choices, the custom types should be registered for polymorphic deserialization. Clearly, the approach using the JsonDerivedType attribute is not viable, as users cannot annotate either `ToolBehavior` or `FunctionCallChoice` SK classes. However, they could register their custom type resolver that would register their custom type(s) if they had access to JsonSerializerOptions used by JsonSerializer during deserialization. Unfortunately, SK does not expose those options publicly today. Even if it had, there are YAML prompts that are deserialized by the YamlDotNet library that would require same custom types supplied via YAML specific deserializer extensibility mechanisms - YamlTypeConverter. This would mean that if a user wants the same custom function calling choice to be used in both YAML and JSON prompts, they would have to register the same custom type twice - for JSON via a custom type resolver and for YAML via a custom YamlTypeConverter. That would also require a mechanism of supplying custom resolvers/converters to all SK `CreateFunctionFrom*Prompt` extension methods.

### Support in YAML prompts
YamlDotNet uses a slightly different approach for polymorphic deserialization out of the box, utilizing YAML tags. You can find more details at this link: https://github.com/aaubry/YamlDotNet/issues/343. So, below is the YAML variant of the JSON above. Note that there is no 'type' property, and YAML tags !function_call_behavior and !auto are used instead:
```yaml
execution_settings:
  default:
    temperature: 0.4
      !function_call_behavior
      choice: !auto
        functions:
          - p1.f1
```

### Tool behavior section location
SK prompts may have one or more entries, one per service, of execution settings to describe service-specific configurations in a prompt. Considering that each section is deserialized to an instance of the `PromptExecutionSettings` class and that class is used by the corresponding service, it makes sense to specify the tool behavior in each service configuration section. On the other hand, this may introduce unnecessary duplication because all services might need exactly the same behavior. Additionally, there could be scenarios where 2 out of 3 services use the same tool behavior configuration, while the remaining one uses a different one.
```json
"tool_behavior":{
    ...
},
"execution_settings": {
   "default": {
     "temperature": 0,
     "tool_behavior":{
        ...
     }
   },
   "gpt-3.5-turbo": {
     "model_id": "gpt-3.5-turbo-0613",
     "temperature": 0.1,
     "tool_behavior":{
        ...
     }
   },
   "gpt-4": {
     "model_id": "gpt-4-1106-preview",
     "temperature": 0.3,
     "tool_behavior":{
        ...
     }
   }
 }
```
To accommodate the scenarios above, it makes sense to introduce an inheritance mechanism that would inherit parent tool behavior configuration if specified on the parent. Regardless of whether the parent has tool behavior configurations or not, it should be possible to specify or override the parent one at each service entry level.

## Option 2
Explore the possibility of resolving specific types at a later post-deserialization phase and in a location with access to a kernel instance, so no polymorphic deserialization would be required. This would allow for the resolution of custom classes registered by users in the kernel service collection. Users will simply register the custom classes that will be automatically picked either during prompt rendering or at the moment the information is required, regardless of the prompt format - JSON or YAML.

## Questions
- Today, the existing tool call behavior can accept and advertise [OpenAI functions](https://github.com/microsoft/semantic-kernel/blob/0296329886eb2116a66e5362f2cc72b42ee30157/dotnet/src/Connectors/Connectors.OpenAI/ToolCallBehavior.cs#L68). These functions are not registered in SK, and SK can only invoke them in 'manual' mode; the 'auto' mode requires the function to be registered on the kernel and throws an exception if that is not the case. Do we have a scenario that requires this functionality?

## Decision Outcome
There were a few decisions taken during the ADR review:
- The Breaking glass support is out of scope. It may be added later if/when needed.
- The `PromptExecution.ToolBehaviors` property should support only one behavior. The original design described in Option 1 supported multiple tool behaviors configured per service. However, it was pointed out that this might not be necessary, could confuse SK users, and adds unnecessary complexity that degrades developer experience.
