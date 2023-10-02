---
# These are optional elements. Feel free to remove any of them.
status: accepted
date: 2023-10-02
deciders: shawncal, rbarreto
consulted: semenshi, dmytrostruk
informed:
---

# Function Running Abstraction

## Context and Problem Statement

Today there's not an abstraction to run/search functions and most of the internal implementations rely its own implementation to find and discover functions using SKContext.

### Problem:

Currently Invoking functions outside of Kernel using the `ISKFunction.InvokeAsync` don't give exposure and support for events and other features that are available when invoking functions from within the Kernel.

Many internal components (like `PromptTemplateEngine` and `Plan`s) implementation don't use Kernel, calling functions directly which also means that they don't support event triggering for example.

The internal implementations currently uses `SKContext` instances which already exposes the Kernel instance and can be used to invoke other functions using the `RunAsync` and be able to support events and other features that are available when invoking functions from within the Kernel.

### Solution:

This change addes the Runner abstraction which will be responsible to search and run functions from other components in the execution context, benefiting components like: TemplateEngine, Plans, Plugins, ...

This also removes the `IKernel` replacing it `IFunctionRunner` abstraction which simplifies and only expose functions
reponsible to run/execute functions from another function in the execution context
of exposure to Kernel fuctions in the `SKContext` .

Calling functions using the `IFunctionRunner` will be the path forward replacing the current `ISKFunction.InvokeAsync` with the `SKContext.IFunctionRunner.RunAsync`.

This changes also makes `Kernel` instance an implementer of `IFunctionRunner` interface and the `SKContext` will be responsible to expose the `IFunctionRunner` instance.

```csharp
interface IFunctionRunner
{
    Task<KernelResult> RunAsync(
    ISKFunction skFunction,
    ContextVariables variables,
    RequestSettings requestSettings,
    CancellationToken cancellationToken = default);

    // This ones abstract the need to have a function instance with internal impl to find & run a function by name.
    Task<KernelResult> RunAsync(
    string pluginName,
    string functionName,
    ContextVariables variables,
    RequestSettings requestSettings,
    CancellationToken cancellationToken = default);
}

interface IKernel : IFunctionRunner
{
    ...
}

```

## Decision Drivers

Have a new Runner abstraction which can be used to run functions from other components.
Simplification of implementations and dependencies.
A step forward moving from `ISKFunction.InvokeAsync` to `IKernel.RunAsync` approach on our internal implementations

Examples:

## Template Engine (CodeBlock.cs)

Current state depends strongly on SKContext and ISKFunction.InvokeAsync

From

```csharp
private async Task<string> RenderFunctionCallAsync(FunctionIdBlock fBlock, SKContext context)
{
    if (context.Functions == null)
    {
        throw new SKException("Function collection not found in the context");
    }

    if (!this.GetFunction(context.Functions!, fBlock, out ISKFunction? function))
    {
        var errorMsg = $"Function `{fBlock.Content}` not found";
        this.Logger.LogError(errorMsg);
        throw new SKException(errorMsg);
    }
    SKContext contextClone = context.Clone();

    // If the code syntax is {{functionName $varName}} use $varName instead of $input
    // If the code syntax is {{functionName 'value'}} use "value" instead of $input
    if (this._tokens.Count > 1)
    {
        contextClone = this.PopulateContextWithFunctionArguments(contextClone);
    }

    try
    {
        await function!.InvokeAsync(contextClone).ConfigureAwait(false);
    }
    catch (Exception ex)
    {
        this.Logger.LogError(ex, "Function {Plugin}.{Function} execution failed with error {Error}", function!.PluginName, function.Name, ex.Message);
        throw;
    }

    return contextClone.Result;
}
```

To

- Removes the responsibility on Searching for functions
- No more dependency on SKContext
- Usage of the IFunctionRunner abstraction to Run functions (Kernel behind the scenes)

```csharp
private async Task<string> RenderFunctionCallAsync(FunctionIdBlock fBlock, ContextVariables variables, IFunctionRunner runner)
{
    if (context.Functions == null)
    {
        throw new SKException("Function collection not found in the context");
    }

    if (!this.GetFunction(context.Functions!, fBlock, out ISKFunction? function))

    ContextVariables inputVariables = variables.Clone();

    // If the code syntax is {{functionName $varName}} use $varName instead of $input
    // If the code syntax is {{functionName 'value'}} use "value" instead of $input
    if (this._tokens.Count > 1)
    {
        inputVariables = this.PopulateContextWithFunctionArguments(inputVariables);
    }

    try
    {
        var kernelResult = await runner.RunAsync(fBlock.PluginName, fBlock.FunctionName, inputVariables).ConfigureAwait(false);
        kernelResult.GetValue<string>();
    }
    catch (Exception ex)
    {
        this.Logger.LogError(ex, "Function {Plugin}.{Function} execution failed with error {Error}", function!.PluginName, function.Name, ex.Message);
        throw;
    }
}
```

## Plugins / Functions

### LanguageCalculatorPlugin.cs

From:

```csharp
var result = await context.Kernel.RunAsync(input, this._mathTranslator).ConfigureAwait(false);
```

To:

```csharp
var result = await context.Runner.RunAsync(this._mathTranslator, input).ConfigureAwait(false);
```

## Plans

Simplify calls to functions from within plans, removes the dependency on managing and creating SKContext, uses the Runner abstraction to run step functions.

### Plan.cs

From:

```csharp
var functionVariables = this.GetNextStepVariables(context.Variables, this);
var functionContext = new SKContext(context.Kernel, functionVariables, context.Functions);

// Execute the step
result = await this.Function
    .WithInstrumentation(context.LoggerFactory)
    .InvokeAsync(functionContext, requestSettings, cancellationToken)
    .ConfigureAwait(false);
```

To:

```csharp

var functionVariables = this.GetNextStepVariables(context.Variables, this);
// Execute the step
result = await context.Runner.RunAsync(
    this.Function.WithInstrumentation(context.LoggerFactory),
    functionVariables,
    requestSettings,
    cancellationToken)
    .ConfigureAwait(false);

```
