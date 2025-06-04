---
# These are optional elements. Feel free to remove any of them.
status: accepted
contact: dmytrostruk
date: 2024-04-24
deciders: sergeymenshykh, markwallace, rbarreto, dmytrostruk, stoub
---

# Exception handling in filters

## Context and Problem Statement

In .NET version of Semantic Kernel, when kernel function throws an exception, it will be propagated through execution stack until some code will catch it. To handle exception for `kernel.InvokeAsync(function)`, this code should be wrapped in `try/catch` block, which is intuitive approach how to deal with exceptions.

Unfortunately, `try/catch` block is not useful for auto function calling scenario, when a function is called based on some prompt. In this case, when function throws an exception, message `Error: Exception while invoking function.` will be added to chat history with `tool` author role, which should provide some context to LLM that something went wrong.

There is a requirement to have the ability to override function result - instead of throwing an exception and sending error message to AI, it should be possible to set some custom result, which should allow to control LLM behavior.

## Considered Options

### [Option 1] Add new method to existing `IFunctionFilter` interface

Abstraction:

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

### [Option 2] Introduce new `IExceptionFilter` interface

New interface will allow to receive exception objects, cancel exception or rethrowing new type of exception. This option can be also added later as filter on a higher level for global exception handling.

Abstraction:

```csharp
public interface IExceptionFilter
{
    // ExceptionContext class will contain information about actual exception, kernel function etc.
    void OnException(ExceptionContext context);
}
```

Usage:

```csharp
public class MyFilter : IFunctionFilter, IExceptionFilter
{
    public void OnFunctionInvoking(FunctionInvokingContext context) { }

    public void OnFunctionInvoked(FunctionInvokedContext context) { }

    public void OnException(ExceptionContext context) {}
}
```

Advantages:

- It's not a breaking change, and all exception handling logic should be added on top of existing filter mechanism.
- Similar to `IExceptionFilter` API in ASP.NET.

Disadvantages:

- It may be not intuitive and hard to remember, that for exception handling, separate interface should be implemented.

### [Option 3] Extend Context model in existing `IFunctionFilter` interface

In `IFunctionFilter.OnFunctionInvoked` method, it's possible to extend `FunctionInvokedContext` model by adding `Exception` property. In this case, as soon as `OnFunctionInvoked` is triggered, it will be possible to observe whether there was an exception during function execution.

If there was an exception, users could do nothing and the exception will be thrown as usual, which means that in order to handle it, function invocation should be wrapped with `try/catch` block. But it will be also possible to cancel that exception and override function result, which should provide more control over function execution and what is passed to LLM.

Abstraction:

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
            // Possible options to handle it:

            // 1. Do not throw an exception that occurred during function execution
            context.Exception = null;

            // 2. Override the result with some value, that is meaningful to LLM
            context.Result = new FunctionResult(context.Function, "Friendly message instead of exception");

            // 3. Rethrow another type of exception if needed - Option 1.
            context.Exception = new Exception("New exception");

            // 3. Rethrow another type of exception if needed - Option 2.
            throw new Exception("New exception");
        }
    }
}
```

Advantages:

- Requires minimum changes to existing implementation and also it won't break existing filter users.
- Similar to `IActionFilter` API in ASP.NET.
- Scalable, because it will be possible to extend similar Context models for other type of filters when needed (prompt or function calling filters).

Disadvantages:

- Not .NET-friendly way of exception handling with `context.Exception = null` or `context.Exception = new AnotherException()`, instead of using native `try/catch` approach.

### [Option 4] Change `IFunctionFilter` signature by adding `next` delegate.

This approach changes the way how filters work at the moment. Instead of having two `Invoking` and `Invoked` methods in filter, there will be only one method that will be invoked during function execution with `next` delegate, which will be responsible to call next registered filter in pipeline or function itself, in case there are no remaining filters.

Abstraction:

```csharp
public interface IFunctionFilter
{
    Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next);
}
```

Usage:

```csharp
public class MyFilter : IFunctionFilter
{
    public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
    {
        // Perform some actions before function invocation
        await next(context);
        // Perform some actions after function invocation
    }
}
```

Exception handling with native `try/catch` approach:

```csharp
public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
{
    try
    {
        await next(context);
    }
    catch (Exception exception)
    {
        this._logger.LogError(exception, "Something went wrong during function invocation");

        // Example: override function result value
        context.Result = new FunctionResult(context.Function, "Friendly message instead of exception");

        // Example: Rethrow another type of exception if needed
        throw new InvalidOperationException("New exception");
    }
}
```

Advantages:

- Native way how to handle and rethrow exceptions.
- Similar to `IAsyncActionFilter` and `IEndpointFilter` API in ASP.NET.
- One filter method to implement instead of two (`Invoking/Invoked`) - this allows to keep invocation context information in one method instead of storing it on class level. For example, to measure function execution time, `Stopwatch` can be created and started before `await next(context)` call and used after the call, while in approach with `Invoking/Invoked` methods the data should be passed between filter actions in other way, for example setting it on class level, which is harder to maintain.
- No need in cancellation logic (e.g. `context.Cancel = true`). To cancel the operation, simply don't call `await next(context)`.

Disadvantages:

- Remember to call `await next(context)` manually in all filters. If it's not called, next filter in pipeline and/or function itself won't be called.

## Decision Outcome

Proceed with Option 4 and apply this approach to function, prompt and function calling filters.
