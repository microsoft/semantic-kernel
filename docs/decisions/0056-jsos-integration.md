---
# These are optional elements. Feel free to remove any of them.
status: accepted
contact: sergeymenshykh
date: 2024-10-03
deciders: sergeymenshykh, westey-m, markwallace
consulted: stephentoub, eiriktsarpalis
informed:
---

# Considering Ways to Integrate JsonSerializerOptions into SK

## Context and Problem Statement
Today, SK relies on JSON serialization and schema generation functionality to generate schemas for function parameters and return types, deserialize them from JSON to the target types as part of the marshaling process, serialize AI models to SK and back, etc.   
  
At the moment, the serialization code either uses no JsonSerializerOptions (JSOs) or uses hardcoded predefined ones for specific purposes without the ability to provide custom ones. This works perfectly fine for non-AOT scenarios where JSON serialization uses reflection by default. However, in Native AOT apps, which do not support all required reflection APIs, reflection-based serialization won't work and will crash.  
   
To enable serialization for Native-AOT scenarios, all serialization code should use source-generated context contracts represented by the `JsonSerializerContext` base class. See the article [How to use source generation in System.Text.Json](https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/source-generation?pivots=dotnet-8-0#specify-source-generation-mode) for more details. Additionally, there should be a way to supply those source-generated classes via the SK public API surface down to the JSON serialization functionality.  
   
This ADR outlines potential options for passing JSOs with configured source-generated contracts down to the JSON serialization code of Native-AOT enabled SK components.

## Decision Drivers

- It's possible to provide external source-generated context contracts down to SK JSON serialization functionality.
- It's intuitively clear and easy to supply source-generated context contracts to SK components. 

## Considered Options

- Option #1: One global JSOs for all SK components
- Option #2: JSOs per SK component
- Option #3: JSOs per SK component operation

## Option #1: One global JSOs for all SK components
This options presumes adding the new `JsonSerializerOptions` property of `JsonSerializerOptions` type to `Kernel` class. All external source-generated context contracts will be registered there and all SK components requiring JSOs will resolve them from there:

```csharp
public sealed class MyPlugin { public Order CreateOrder() => new(); }

public sealed class Order { public string? Number { get; set; } }

[JsonSerializable(typeof(Order))]
internal sealed partial class OrderJsonSerializerContext : JsonSerializerContext
{
}

public async Task TestAsync()
{
    JsonSerializerOptions options = new JsonSerializerOptions();
    options.TypeInfoResolverChain.Add(OrderJsonSerializerContext.Default);

    Kernel kernel = new Kernel();
    kernel.JsonSerializerOptions = options;

    // All the following Kernel extension methods use JSOs configured on the `Kernel.JsonSerializerOptions` property
    kernel.CreateFunctionFromMethod(() => new Order());
    kernel.CreateFunctionFromPrompt("<prompt>");
    kernel.CreatePluginFromFunctions("<plugin>", [kernel.CreateFunctionFromMethod(() => new Order())]);
    kernel.CreatePluginFromType<MyPlugin>("<plugin>");
    kernel.CreatePluginFromPromptDirectory("<directory>", "<plugin>");
    kernel.CreatePluginFromObject(new MyPlugin(), "<plugin>");

    // AI connectors can use the `Kernel.JsonSerializerOptions` property as well
    var onnxService = new OnnxRuntimeGenAIChatCompletionService("<modelId>", "<modelPath>");
    var res = await onnxService.GetChatMessageContentsAsync(new ChatHistory(), new PromptExecutionSettings(), kernel);

    // The APIs below can't use the `Kernel.JsonSerializerOptions` property because they don't have access to the `Kernel` instance
    KernelFunctionFactory.CreateFromMethod(() => new Order(), options);
    KernelFunctionFactory.CreateFromPrompt("<prompt>", options);

    KernelPluginFactory.CreateFromObject(new MyPlugin(), options, "<plugin>");
    KernelPluginFactory.CreateFromType<MyPlugin>(options, "<plugin>");
    KernelPluginFactory.CreateFromFunctions("<plugin>", [kernel.CreateFunctionFromMethod(() => new Order())]);
}
```

Pros:  
- All SK components use JSOs configured in one place. A kernel clone with different options can be provided if required.  
   
Cons:  
- May require changing the SK component to depend on the kernel if not already.  
- Depending on how JSOs are initialized, this option might not be as explicit as others regarding the usage of non-AOT compatible APIs in an AOT app, leading to trial-and-error to register source-generated contracts based on runtime errors.  
- Similar to the above, it may not be clear which component/API needs JSOs, postponing discovery to runtime.  
- Will add another way of providing JSOs in SK. Low-level KernelFunctionFactory and KernelPluginFactory accept JSOs via method parameters.  
- SK AI connectors accept an **optional** instance of the kernel in their operation, which sends mixed signals. On one hand, it's optional, meaning AI connectors can work without it; on the other hand, the operation will fail in an AOT app if no kernel is provided.
- SK components that accept JSOs via Kernel as a parameter of operations, rather than as a parameter of a constructor, and that need to combine external source-generated contexts with internal ones, will combine them at the first invocation of the operation and cache the result for subsequent operation invocations. This may be misleading because the operation can accept a new JSO instance per invocation, but the component will only use the first cached one.

### Ways to Provide JSON Serializer Options (JSOs) to the Kernel:
1. Via `Kernel` constructor.
    ```csharp
    private readonly JsonSerializerOptions? _serializerOptions = null;

    // Existing AOT incompatible constructor
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of JSON serialization in SK, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of JSON serialization in SK, making it incompatible with AOT scenarios.")]
    public Kernel(IServiceProvider? services = null,KernelPluginCollection? plugins = null) {}

    // New AOT compatible constructor
    public Kernel(JsonSerializerOptions jsonSerializerOptions, IServiceProvider? services = null,KernelPluginCollection? plugins = null) 
    { 
        this._serializerOptions = jsonSerializerOptions;
        this._serializerOptions.MakeReadOnly(); // Prevent mutations that may not be picked up by SK components created with initial JSOs.
    }

    public JsonSerializerOptions JsonSerializerOptions => this._serializerOptions ??= JsonSerializerOptions.Default;
    ```
    Pros:
    - AOT related warnings will be shown for the usage of a non-AOT compatible constructor at compile time.

2. Via the `Kernel.JsonSerializerOptions` property setter
    ```csharp
    private readonly JsonSerializerOptions? _serializerOptions = null;

    public JsonSerializerOptions JsonSerializerOptions
    {
        get
        {
            return this._serializerOptions ??= ??? // JsonSerializerOptions.Default will work for non-AOT scenarios and will fail in AOT ones.
        }
        set
        {
            value.MakeReadOnly(true); // prevent future modifications
            this._serializerOptions = value;
        }
    }
    ```
    Cons:
    - No AOT warning will be generated during kernel initialization in the AOT application, leading to a runtime failure.
    - JSOs assigned after an SK component (KernelFunction accepts JSOs via the constructor) is created won't be picked up by the component.

3. DI
    TBD after requirements are fleshed out.

## Option #2: JSOs per SK component
This option presumes supplying JSOs at the component's instantiation site or constructor:
```csharp
    public sealed class Order { public string? Number { get; set; } }

    [JsonSerializable(typeof(Order))]
    internal sealed partial class OrderJsonSerializerContext : JsonSerializerContext
    {
    }

    JsonSerializerOptions options = new JsonSerializerOptions();
    options.TypeInfoResolverChain.Add(OrderJsonSerializerContext.Default);

    // All the following kernel extension methods accept JSOs explicitly supplied as an argument for the corresponding parameter:
    kernel.CreateFunctionFromMethod(() => new Order(), options);
    kernel.CreateFunctionFromPrompt("<prompt>", options);
    kernel.CreatePluginFromFunctions("<plugin>", [kernel.CreateFunctionFromMethod(() => new Order(), options)]);
    kernel.CreatePluginFromType<MyPlugin>("<plugin>", options);
    kernel.CreatePluginFromPromptDirectory("<directory>", "<plugin>", options);
    kernel.CreatePluginFromObject(new MyPlugin(), "<plugin>", options);

    // The AI connectors accept JSOs at the instantiation site rather than at the invocation site.
    var onnxService = new OnnxRuntimeGenAIChatCompletionService("<modelId>", "<modelPath>", options);
    var res = await onnxService.GetChatMessageContentsAsync(new ChatHistory(), new PromptExecutionSettings());

    // The APIs below already accept JSOs at the instantiation site.
    KernelFunctionFactory.CreateFromMethod(() => new Order(), options);
    KernelFunctionFactory.CreateFromPrompt("<prompt>", options);

    KernelPluginFactory.CreateFromObject(new MyPlugin(), options, "<plugin>");
    KernelPluginFactory.CreateFromType<MyPlugin>(options, "<plugin>");
    KernelPluginFactory.CreateFromFunctions("<plugin>", [kernel.CreateFunctionFromMethod(() => new Order())]);
```
Pros:
- AOT warnings will be generated at compile time at each component instantiation site.
- Same way of working with JSOs across all SK components.
- Each component will combine external source-generated contexts with internal ones at instantiation time and the result will be used by all it's operations.
- Does't require SK components to depend on Kernel.

Cons:
- There's no one central place to register source-generated contexts

## Option #3: JSOs per SK component operation
This option presumes supplying JSOs at component operation invocation sites rather than at instantiation sites.

Pros:
- AOT warnings will be generated during compile time at each component operation invocation site.

Cons:
- New operations/methods overloads accepting JSOs will have to be added for all SK components requiring external source-generated contracts.
- If components need to combine internal and external source-generated contexts, it can be inefficient if done per operation invocation or semantically incorrect if the first JSOs are cached and used for subsequent invocations.
- Will add another way of providing JSOs in SK. Low-level KernelFunctionFactory and KernelPluginFactory accept JSOs via method parameters.  
- Not applicable to all SK components. KernelFunction needs JSOs before it is invoked for schema generation purposes. 

## Decision Outcome
TBD