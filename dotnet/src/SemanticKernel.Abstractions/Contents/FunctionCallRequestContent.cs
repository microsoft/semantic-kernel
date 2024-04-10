// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a function call requested by LLM.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class FunctionCallRequestContent : KernelContent
{
    /// <summary>
    /// The function call ID.
    /// </summary>
    public string? Id { get; }

    /// <summary>
    /// The plugin name.
    /// </summary>
    public string? PluginName { get; }

    /// <summary>
    /// The function name.
    /// </summary>
    public string FunctionName { get; }

    /// <summary>
    /// The kernel arguments.
    /// </summary>
    public KernelArguments? Arguments { get; }

    /// <summary>
    /// The exception that occurred while mapping original LLM function call request to the model class.
    /// </summary>
    public Exception? Exception { get; init; }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallRequestContent"/> class.
    /// </summary>
    /// <param name="functionName">The function name.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="id">The function call ID.</param>
    /// <param name="arguments">The function original arguments.</param>
    [JsonConstructor]
    public FunctionCallRequestContent(string functionName, string? pluginName = null, string? id = null, KernelArguments? arguments = null)
    {
        Verify.NotNull(functionName);

        this.FunctionName = functionName;
        this.Id = id;
        this.PluginName = pluginName;
        this.Arguments = arguments;
    }

    /// <summary>
    /// Invokes the function represented by the function call content type.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function's execution.</returns>
    public async Task<FunctionCallResultContent> InvokeAsync(Kernel kernel, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel, nameof(kernel));

        if (this.Exception is not null)
        {
            return new FunctionCallResultContent(this, this.Exception.Message);
        }

        if (kernel.Plugins.TryGetFunction(this.PluginName, this.FunctionName, out KernelFunction? function))
        {
            var result = await function.InvokeAsync(kernel, this.Arguments, cancellationToken).ConfigureAwait(false);

            return new FunctionCallResultContent(this, result);
        }

        throw new KeyNotFoundException($"The plugin collection does not contain a plugin and/or function with the specified names. Plugin name - '{this.PluginName}', function name - '{this.FunctionName}'.");
    }
}
