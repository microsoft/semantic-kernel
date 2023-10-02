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

Today there no dedicated abstraction to run available functions.
This brings a problem because many components has its own implementation to find, discover and invoke functions.

### Problem:

Currently Invoking functions using the `ISKFunction.InvokeAsync` happens outside of the Kernel which don't give exposure and support for events and other features that are available when invoking functions from within the Kernel `RunAsync`.

Many internal components (like `PromptTemplateEngine` and `Plan`) implementation don't use Kernel `RunAsync` and need to be changed. 

Usage of `SKContext` instances today already exposes the `Kernel/Runner` instance thru a property, this allows many of current services that depends on `SKContext` to invoke other functions using the `RunAsync` instead of `InvokeAsync`.

### Solution:

Instead of using `IKernel` interface directly we added a new `IFunctionRunner` abstraction which will be only responsible to Run functions,

Make `Kernel` class an implementer of `IFunctionRunner` abstraction.

Change `SKContext.Kernel` to `SKContext.Runner` property which simplifies and only expose methods reponsible to run/execute functions.

Calling functions using the `IFunctionRunner` is the path forward replacing the current `ISKFunction.InvokeAsync` with the `SKContext.IFunctionRunner.RunAsync` in components like `PromptTemplateEngine`, `Plan` and Plugins.


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

## Examples:

#### Template Engine (CodeBlock.cs)

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

### Plugins / Functions

#### LanguageCalculatorPlugin.cs

From:

```csharp
var result = await context.Kernel.RunAsync(input, this._mathTranslator).ConfigureAwait(false);
```

To:

```csharp
var result = await context.Runner.RunAsync(this._mathTranslator, input).ConfigureAwait(false);
```

### Plans

Simplify calls to functions from within plans, removes the dependency on managing and creating SKContext, uses the Runner abstraction to run step functions.

#### Plan.cs

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
