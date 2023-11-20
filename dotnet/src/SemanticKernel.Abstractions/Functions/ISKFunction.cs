// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Semantic Kernel callable function interface
/// </summary>
public interface ISKFunction
{
    /// <summary>
    /// Name of the function. The name is used by the function collection and in prompt templates e.g. {{pluginName.functionName}}
    /// </summary>
    string Name { get; }

    /// <summary>
    /// Function description. The description is used in combination with embeddings when searching relevant functions.
    /// </summary>
    string Description { get; }

    /// <summary>
    /// Model request settings.
    /// </summary>
    IEnumerable<AIRequestSettings> ModelSettings { get; }

    /// <summary>
    /// Gets the metadata describing the function.
    /// </summary>
    /// <returns>An instance of <see cref="SKFunctionMetadata"/> describing the function</returns>
    SKFunctionMetadata GetMetadata();

    /// <summary>
    /// Invoke the <see cref="ISKFunction"/>.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="context">SK context</param>
    /// <param name="requestSettings">LLM completion settings (for semantic functions only)</param>
    /// <returns>The updated context, potentially a new one if context switching is implemented.</returns>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    Task<FunctionResult> InvokeAsync(
        Kernel kernel,
        SKContext context,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default);
}
