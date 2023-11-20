// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
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
public abstract class SKFunction
{
    /// <summary>
    /// Name of the function. The name is used by the function collection and in prompt templates e.g. {{pluginName.functionName}}
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; protected set; } // TODO: make this readonly

    /// <summary>
    /// Function description. The description is used in combination with embeddings when searching relevant functions.
    /// </summary>
    [JsonPropertyName("description")]
    public string Description { get; protected set; }

    /// <summary>
    /// Model request settings.
    /// </summary>
    [JsonPropertyName("model_settings")]
    public IEnumerable<AIRequestSettings> ModelSettings { get; protected set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="SKFunction"/> class.
    /// </summary>
    /// <param name="name">Name of the function.</param>
    /// <param name="description">Function description.</param>
    /// <param name="modelSettings">Model request settings.</param>
    internal SKFunction(string name, string description, IEnumerable<AIRequestSettings>? modelSettings = null)
    {
        this.Name = name;
        this.Description = description;
        this.ModelSettings = modelSettings ?? Enumerable.Empty<AIRequestSettings>();
    }

    /// <summary>
    /// Returns a description of the function, including parameters.
    /// </summary>
    /// <returns>An instance of <see cref="FunctionView"/> describing the function</returns>
    abstract public FunctionView Describe();

    /// <summary>
    /// Invoke the <see cref="SKFunction"/>.
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
