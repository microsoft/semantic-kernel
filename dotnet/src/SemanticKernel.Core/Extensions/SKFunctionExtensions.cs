// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130 // Namespace does not match folder structure

/// <summary>
/// Class that holds extension methods for objects implementing ISKFunction.
/// </summary>
public static class SKFunctionExtensions
{
    /// <summary>
    /// Configure the LLM settings used by semantic function.
    /// </summary>
    /// <param name="skFunction">Semantic function</param>
    /// <param name="requestSettings">Request settings</param>
    /// <returns>Self instance</returns>
    public static ISKFunction UseCompletionSettings(this ISKFunction skFunction, AIRequestSettings requestSettings)
    {
        return skFunction.SetAIConfiguration(requestSettings);
    }

    /// <summary>
    /// Execute a function allowing to pass the main input separately from the rest of the context.
    /// </summary>
    /// <param name="function">Function to execute</param>
    /// <param name="kernel">Kernel</param>
    /// <param name="variables">Input variables for the function</param>
    /// <param name="functions">Collection of functions that this function can access</param>
    /// <param name="culture">Culture to use for the function execution</param>
    /// <param name="requestSettings">LLM completion settings (for semantic functions only)</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function execution</returns>
    public static Task<FunctionResult> InvokeAsync(this ISKFunction function,
        IKernel kernel,
        ContextVariables? variables = null,
        IReadOnlyFunctionCollection? functions = null,
        CultureInfo? culture = null,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        var context = new SKContext(kernel, variables, functions ?? kernel.Functions)
        {
            Culture = culture!
        };

        return function.InvokeAsync(context, requestSettings ?? function.RequestSettings, cancellationToken);
    }

    /// <summary>
    /// Execute a function allowing to pass the main input separately from the rest of the context.
    /// </summary>
    /// <param name="function">Function to execute</param>
    /// <param name="input">Input string for the function</param>
    /// <param name="kernel">Kernel</param>
    /// <param name="functions">Collection of functions that this function can access</param>
    /// <param name="culture">Culture to use for the function execution</param>
    /// <param name="requestSettings">LLM completion settings (for semantic functions only)</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function execution</returns>
    public static Task<FunctionResult> InvokeAsync(this ISKFunction function,
        string input,
        IKernel kernel,
        IReadOnlyFunctionCollection? functions = null,
        CultureInfo? culture = null,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
        => function.InvokeAsync(kernel, new ContextVariables(input), functions, culture, requestSettings, cancellationToken);

    /// <summary>
    /// Returns decorated instance of <see cref="ISKFunction"/> with enabled instrumentation.
    /// </summary>
    /// <param name="function">Instance of <see cref="ISKFunction"/> to decorate.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public static ISKFunction WithInstrumentation(this ISKFunction function, ILoggerFactory? loggerFactory = null)
    {
        return new InstrumentedSKFunction(function, loggerFactory);
    }
}
