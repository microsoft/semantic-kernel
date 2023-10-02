# One way to call functions using Semantic Kernel

## Problem (Who to call? InvokeAsync or RunAsync?)

Today we have two ways of calling functions and is not clear which one to use and what are the differences between them. This lack of clarity makes it difficult to:

- Have a unified design to the Project centered around the Kernel as the single source of truth to Run functions.
- Understand clearly the lifecycle of a function execution.
- When and what scope of services will be used by the function.

## ISKFunction - Invoke Async problem.

ISKFunction is an abstraction and initially intented to be used to call functions from within the Kernel allowing it call the functions abstractions as a pipeline combining the I/O from multiple functions.

For some reason ISKFunction.InvokeAsync calls started to be used by components without the `Kernel` dependency.

### InvokeAsync without Kernel

A Kernel instance should manage the discoverability but that's not the case today.

1. When the functions are called directly the Idea of a Kernel manager of lifecycle and services reference/availability breaks up.
1. There are no benefits of calling functions thru the abstraction if the caller can call the functions directly
1. Semantic Functions are difficult to be created and called without a Kernel instance, and there are no benefit in doing so.
1. InvokeAsync requires SKContext which is only possible to create using a Kernel instance (`kernel.CreateNewContext()`).

### IKernel.RunAsync problem.

The `IKernel.RunAsync` implementation today don't expose its services and configuration automatically to functions. 

This means that the function will not have access to the services and configuration of the Kernel instance that is running it.

Currently RunAsync method cannot accept the RequestSettings overload which means that the caller cannot change the settings from the functions being called, many invocations using the `ISKFunction.InvokeAsync` passes the `RequestSettings` as a parameter.

## Semantic Functions Problem 

**Factories are stored in Semantic Functions instance initialization**

Semantic Functions instance currently hold the service factories during initialization. This creates a problem because **a function will not use/respect the services available in the Kernel** but will rather use the service configuration it was initialized with.

This becomes even more problematic when the same function is used across multiple Kernels with different services/configurations.

## Solution

### Kernel is the only way to call functions

The function will respect the services and configuration of available to the Kernel instance that is running it. 

If the ISKFunction configuration ask for a service that is not available in the Kernel the Run will fail.

### Major Implementation changes

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
    
    The function will respect the services and configuration of the Kernel instance that is running it. If the ISKFunction configuration don't ask for a service that is not available in the Kernel the Run will fail.
