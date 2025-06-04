// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a function call requested by AI model.
/// </summary>
public sealed class FunctionCallContent : KernelContent
{
    /// <summary>
    /// The function call ID.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Id { get; }

    /// <summary>
    /// The plugin name.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? PluginName { get; }

    /// <summary>
    /// The function name.
    /// </summary>
    public string FunctionName { get; }

    /// <summary>
    /// The kernel arguments.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public KernelArguments? Arguments { get; }

    /// <summary>
    /// The exception that occurred while mapping original AI model function call to the model class.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public Exception? Exception { get; init; }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="functionName">The function name.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="id">The function call ID.</param>
    /// <param name="arguments">The function original arguments.</param>
    [JsonConstructor]
    public FunctionCallContent(string functionName, string? pluginName = null, string? id = null, KernelArguments? arguments = null)
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
    public async Task<FunctionResultContent> InvokeAsync(Kernel kernel, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel, nameof(kernel));

        if (this.Exception is not null)
        {
            throw this.Exception;
        }

        if (kernel.Plugins.TryGetFunction(this.PluginName, this.FunctionName, out KernelFunction? function))
        {
            var result = await function.InvokeAsync(kernel, this.Arguments, cancellationToken).ConfigureAwait(false);

            return new FunctionResultContent(this, result);
        }

        throw new KeyNotFoundException($"The plugin collection does not contain a plugin and/or function with the specified names. Plugin name - '{this.PluginName}', function name - '{this.FunctionName}'.");
    }

    /// <summary>
    /// Returns list of function calls provided via <see cref="ChatMessageContent.Items"/> collection.
    /// </summary>
    /// <param name="messageContent">The <see cref="ChatMessageContent"/>.</param>
    /// <returns></returns>
    public static IEnumerable<FunctionCallContent> GetFunctionCalls(ChatMessageContent messageContent)
    {
        return messageContent.Items.OfType<FunctionCallContent>();
    }
}
