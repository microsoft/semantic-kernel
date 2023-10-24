---
# These are optional elements. Feel free to remove any of them.
status: accepted
date: 2023-09-21
deciders: shawncal, dmytrostruk
consulted: 
informed: 
---
# Replace SKContext as Function/Kernel result type with FunctionResult and KernelResult models

## Context and Problem Statement

Methods `function.InvokeAsync` and `kernel.RunAsync` return `SKContext` as result type. This has several problems:

1. `SKContext` contains property `Result`, which is `string`. Based on that, it's not possible to return complex type or implement streaming capability in Kernel.
2. `SKContext` contains property `ModelResults`, which is coupled to LLM-specific logic, so it's only applicable to semantic functions in specific cases.
3. `SKContext` as a mechanism of passing information between functions in pipeline should be internal implementation. Caller of Kernel should provide input/request and receive some result, but not `SKContext`.
4. `SKContext` contains information related to the last executed function without a way to access information about specific function in pipeline.

## Decision Drivers

1. Kernel should be able to return complex type as well as support streaming capability.
2. Kernel should be able to return data related to function execution (e.g. amount of tokens used) in a way, when it's not coupled to AI logic.
3. `SKContext` should work as internal mechanism of passing information between functions.
4. There should be a way how to differentiate function result from kernel result, since these entities are different by nature and may contain different set of properties in the future.
5. The possibility to access specific function result in the middle of pipeline will provide more insights to the users how their functions performed.

## Considered Options

1. Use `dynamic` as return type - this option provides some flexibility, but on the other hand removes strong typing, which is preferred option in .NET world. Also, there will be no way how to differentiate function result from Kernel result.
2. Define new types - `FunctionResult` and `KernelResult` - chosen approach.

## Decision Outcome

New `FunctionResult` and `KernelResult` return types should cover scenarios like returning complex types from functions, supporting streaming and possibility to access result of each function separately.

### Complex Types and Streaming

For complex types and streaming, property `object Value` will be defined in `FunctionResult` to store single function result, and in `KernelResult` to store result from last function in execution pipeline. For better usability, generic method `GetValue<T>` will allow to cast `object Value` to specific type.

Examples:

```csharp
// string
var text = (await kernel.RunAsync(function)).GetValue<string>();

// complex type
var myComplexType = (await kernel.RunAsync(function)).GetValue<MyComplexType>();

// streaming
var results = (await kernel.RunAsync(function)).GetValue<IAsyncEnumerable<int>>();

await foreach (var result in results)
{
    Console.WriteLine(result);
}
```

When `FunctionResult`/`KernelResult` will store `TypeA` and caller will try to cast it to `TypeB` - in this case `InvalidCastException` will be thrown with details about types. This will provide some information to the caller which type should be used for casting.

### Metadata

To return additional information related to function execution - property `Dictionary<string, object> Metadata` will be added to `FunctionResult`. This will allow to pass any kind of information to the caller, which should provide some insights how function performed (e.g. amount of tokens used, AI model response etc.)

Examples:

```csharp
var functionResult = await function.InvokeAsync(context);
Console.WriteLine(functionResult.Metadata["MyInfo"]);
```

### Multiple function results

`KernelResult` will contain collection of function results - `IReadOnlyCollection<FunctionResult> FunctionResults`. This will allow to get specific function result from `KernelResult`. Properties `FunctionName` and `PluginName` in `FunctionResult` will help to get specific function from collection.

Example:

```csharp
var kernelResult = await kernel.RunAsync(function1, function2, function3);

var functionResult2 = kernelResult.FunctionResults.First(l => l.FunctionName == "Function2" && l.PluginName == "MyPlugin");

Assert.Equal("Result2", functionResult2.GetValue<string>());
```
