// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Semantic Kernel callable function abstract base class.
/// </summary>
public abstract class KernelFunction
{
    /// <summary>
    /// Name of the function. The name is used by the function collection and in prompt templates e.g. {{pluginName.functionName}}
    /// </summary>
    public string Name { get; protected set; }

    /// <summary>
    /// Function description. The description is used in combination with embeddings when searching relevant functions.
    /// </summary>
    public string Description { get; protected set; }

    /// <summary>
    /// Model request settings.
    /// </summary>
    public IEnumerable<AIRequestSettings> ModelSettings { get; protected set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelFunction"/> class.
    /// </summary>
    /// <param name="name">Name of the function.</param>
    /// <param name="description">Function description.</param>
    /// <param name="modelSettings">Model request settings.</param>
    internal KernelFunction(string name, string description, IEnumerable<AIRequestSettings>? modelSettings = null)
    {
        this.Name = name;
        this.Description = description;
        this.ModelSettings = modelSettings ?? Enumerable.Empty<AIRequestSettings>();
    }

    /// <summary>
    /// Gets the metadata describing the function.
    /// </summary>
    /// <returns>An instance of <see cref="SKFunctionMetadata"/> describing the function</returns>
    abstract public SKFunctionMetadata GetMetadata();

    /// <summary>
    /// Invoke the <see cref="KernelFunction"/>.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="context">SK context</param>
    /// <param name="requestSettings">LLM completion settings (for semantic functions only)</param>
    /// <returns>The updated context, potentially a new one if context switching is implemented.</returns>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    abstract public Task<FunctionResult> InvokeAsync(
        Kernel kernel,
        SKContext context,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default);
}
