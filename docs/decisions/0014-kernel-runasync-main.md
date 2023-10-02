# One way to call functions using Semantic Kernel

## Problem (Who to call? InvokeAsync or RunAsync?)

Today we have two ways of calling functions and is not clear which one to use and what are the differences between them. This lack of clarity makes it difficult to:

- Lack of an unified design regarding function execution.
- Understand clearly the lifecycle of a function execution.
- When and what scope of services will be used by the function.

## ISKFunction - Invoke Async problem.

ISKFunction is an abstraction initially intented to be consumed only by the Kernel allowing it call cascade functions as a pipeline, combining the outputs of functions as inputs of the next.

For quite some time ISKFunction.InvokeAsync calls started to be used by internal components without the `Kernel` dependency, which can be a problem for the following reasons:

1. When the functions are called directly the Idea of a Kernel manager of lifecycle and services reference/availability breaks up.
1. There is no benefit in calling an ISKFunction if the caller can call the function directly.
1. Semantic Functions are difficult to be created and called without a Kernel instance.
1. InvokeAsync requires SKContext which is only possible to create using a Kernel instance (`kernel.CreateNewContext(...)`).

### IKernel.RunAsync problem.

The `IKernel.RunAsync` implementation today don't expose services and configuration to functions. 

This means that the function implementations cannot access the services available on the Kernel instance that is running it.

Currently RunAsync method cannot accept the RequestSettings overload which means that the `RunAsync` caller cannot override the settings for functions being called, many invocations using the `ISKFunction.InvokeAsync` passes the `RequestSettings` as a parameter.

## Semantic Functions Problem 

**Factories are stored in Semantic Functions instances during initialization**

This creates a problem because during the `RunAsync` **a function will not use the services available in the Kernel** but the service configuration it was initialized with.

This becomes even more problematic when the same function is used across multiple Kernels with different services/configurations.

## Solution

A Kernel instance should be a container and boudary manager of services available/discoverable by any function it runs

Functions should not have knowledge of the services initialization, Kernel should be responsible to provide the services to the functions it runs.

### Kernel is the only way to call functions

The function will use the Kernel services that are available in the Kernel instance that is running it. If the ISKFunction configuration ask for a service that is not available in the Kernel the Run will fail.

### Solution changes needed

1. SKContext becomes internal and cannot be instantiated outside of the Kernel. This will prevent any attempt to call `ISKFunciton.InvokeAsync` directly.

1. ISKFunctions will not have any more factories in the initialization. 
    
    1. Drop and Obsolete `SetAiService()` from `ISKFunction` interface.

    1. Change `ISKFunction.AIRequestSettings` to be a `ICollection<AIRequestSettings>`, so a function can have multiple settings for each different service. (TemplateEngine, TextCompletion, ChatCompletion, ...)

    1. Add a new property to `ServiceType` to `AIRequestSettings` where it will be the string matching the service interface or the concrete type (will be used by the Kernel to find the service instance in the Kernel context)

    1. Move `TemplateEngineConfig` as a sub set of `AIRequestSettings` where the default for CreateSemanticFunctions will add service type as `PromptTemplateEngine` concrete name. 

    1. Don't instantiate a `PromptTemplateEngine` instance in the `SemanticFunction` constructor, instead Kernel will use the function `AIRequestSettings` to get the `PromptTemplateEngine` service instance during function invocation using the `PromptTemplateConfig` configuration.

    1. SKContext will have a `SKContext.GetService<T>()` method which will provide only the **services required** in the `AIRequestSettings` configuration to get the service instance from the current running Kernel context.

    1. Add to `AIRequestSettings` property with a list of `Dictionary<string, IAIService>` keys identifiers to be used while calling RunAsync, which will be available thru `SKContext.GetService<T>`.

    1. SemanticFunctions implementation changes to Load `IPromptTemplateEngine` from SKContext as well as `ITextCompletion` or `IChatCompletion`.

    1. `IKernel.RunAsync` will check function `AIRequestSettings` dependencies and will create a new `SKContext` instance with the required services and configuration.

        1. `AIRequestSettings -> SemanticFunctionConfig` will be used to load the services and configuration for the function in the invocation context. 

        1. `AIRequestSettings -> PromptTemplateConfig` will be used to load the `IPromptTemplateEngine` service instance in the invocation context.
    
