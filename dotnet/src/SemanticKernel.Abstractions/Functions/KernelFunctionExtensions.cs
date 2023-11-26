// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Functions;

/// <summary>
/// Kernel function extensions class.
/// </summary>
public static class KernelFunctionExtensions
{
    /// <summary>
    /// Invoke the <see cref="KernelFunction"/> in streaming mode.
    /// </summary>
    /// <param name="function">Target function</param>
    /// <param name="kernel">The kernel</param>
    /// <param name="variables">SK context variables</param>
    /// <param name="requestSettings">LLM completion settings (for semantic functions only)</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A asynchronous list of streaming result chunks</returns>
    public static IAsyncEnumerable<StreamingContent> InvokeStreamingAsync(
        this KernelFunction function,
        Kernel kernel,
        ContextVariables? variables = null,
        PromptExecutionSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        return function.InvokeStreamingAsync<StreamingContent>(kernel, variables ?? new ContextVariables(), requestSettings, cancellationToken);
    }
}
