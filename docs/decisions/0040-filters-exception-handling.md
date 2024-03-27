---
# These are optional elements. Feel free to remove any of them.
status: proposed
contact: dmytrostruk
date: 2023-03-26
deciders: sergeymenshykh, markwallace, rbarreto, dmytrostruk
---

# Exception handling in filters

## Context and Problem Statement

In .NET version of Semantic Kernel, when kernel function throws an exception, it will be propagated through execution stack until some code will catch it. To handle exception for `kernel.InvokeAsync(function)`, this code should be wrapped in `try/catch` block, which is intuitive approach how to deal with exceptions.

Unfortunately, `try/catch` block is not useful for auto function calling scenario, when a function is called based on some prompt. In this case, when function throws an exception, message `Error: Exception while invoking function.` will be added to chat history with `tool` author role, which should provide some context to LLM that something went wrong.

There is a requirement to have the ability to override function result - instead of throwing an exception and sending error message to AI, it should be possible to set some custom result, which should allow to control LLM behavior.

## Considered Options

### [Option 1] Introduce new `IExceptionFilter` interface

New interface will allow to receive exception objects and cancel exception throwing.

```csharp
public interface IExceptionFilter
{
    // Option 1.1 - FunctionExceptionContext class will contain information about actual exception and kernel function
    void OnFunctionException(FunctionExceptionContext context);

    // Option 1.2 - FunctionException will be inherited from System.Exception and will contain information about actual exception and kernel function
    void OnFunctionException(FunctionException exception);
}
```

Usage:

```csharp
public class MyFilter : IFunctionFilter, IExceptionFilter
{
    public void OnFunctionInvoking(FunctionInvokingContext context) { }

    public void OnFunctionInvoked(FunctionInvokedContext context) { }

    public void OnFunctionException(...) {}
}
```

Advantages:

- It's not a breaking change, and all exception handling logic should be added on top of existing filter mechanism.

Disadvantages:

- It may be not intuitive and hard to remember, that for exception handling, separate interface should be implemented.
- It's not clear how to scale it in case we would like to add exception handling for function, prompt and other type of filters (e.g. function calling filters).

### [Option 2] Add new method to existing `IFunctionFilter` interface

```csharp
public interface IFunctionFilter
{
    void OnFunctionInvoking(FunctionInvokingContext context);

    void OnFunctionInvoked(FunctionInvokedContext context);

    // New method
    void OnFunctionException(FunctionExceptionContext context);
}
```

Disadvantages:

- Adding new method to existing interface will be a breaking change, as it will force current filter users to implement new method.
- This method will be always required to implement when using function filters, even when exception handling is not needed. On the other hand, this method won't return anything, so it could remain always empty, or with .NET multitargeting, it should be possible to define default implementation for C# 8 and above.

### [Option 3] Extend Context model in existing `IFunctionFilter` interface

In `IFunctionFilter.OnFunctionInvoked` method, it's possible to extend `FunctionInvokedContext` model by adding `Exception` property. In this case, as soon as `OnFunctionInvoked` is triggered, it will be possible to observe whether there was an exception during function execution.

If there was an exception, users could do nothing and the exception will be thrown as usual, which means that in order to handle it, function invocation should be wrapped with `try/catch` block. But it will be also possible to cancel that exception and override function result, which should provide more control over function execution and what is passed to LLM.

```csharp
public sealed class FunctionInvokedContext : FunctionFilterContext
{
    // other properties...

    public Exception? Exception { get; private set; }
}
```

Usage:

```csharp
public class MyFilter : IFunctionFilter
{
    public void OnFunctionInvoking(FunctionInvokingContext context) { }

    public void OnFunctionInvoked(FunctionInvokedContext context)
    {
        // This means that exception occurred during function execution.
        // If we ignore it, the exception will be thrown as usual.
        if (context.Exception is not null)
        {
            // It will be also possible to avoid throwing an exception and override function result.

            // This is the same as context.Exception = null;
            // Although CancelException method feels more user-friendly.
            context.CancelException();

            // This is the result the function will return.
            // In auto function calling scenario, it will be sent to AI instead of error message.
            context.SetResultValue("Some default result.");
        }
    }
}
```

This approach will require minimum changes to existing implementation and also it won't break existing filter users.

Another advantage is that the similar approach is used in ASP.NET action filters, where `ActionExecutedContext` model also has `Exception` property available for error that occurred during action execution, so it should be easier to understand the concept for those who already worked with action filters in ASP.NET.

This approach should be scalable, because it will be possible to extend similar Context models for other type of filters when needed (prompt or function calling filters).

## Decision Outcome

TBD.
