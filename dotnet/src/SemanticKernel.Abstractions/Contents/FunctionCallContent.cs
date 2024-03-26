// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a function call content.
/// </summary>
public sealed class FunctionCallContent : KernelContent
{
    /// <summary>
    /// The function call ID.
    /// </summary>
    public string? Id { get; private set; }

    /// <summary>
    /// The plugin name.
    /// </summary>
    public string? PluginName { get; private set; }

    /// <summary>
    /// The function name.
    /// </summary>
    public string FunctionName { get; private set; }

    /// <summary>
    /// The function arguments.
    /// </summary>
    [EditorBrowsable(EditorBrowsableState.Never)]
    public string? Arguments { get; private set; }

    /// <summary>
    /// Gets the fully-qualified name of the function.
    /// </summary>
    [EditorBrowsable(EditorBrowsableState.Never)]
    public string FullyQualifiedName { get; private set; }

    /// <summary>
    /// The kernel arguments.
    /// </summary>
    [JsonIgnore]
    public KernelArguments? KernelArgument { get; private set; }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="id">The function call ID.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="functionName">The function name.</param>
    /// <param name="fullyQualifiedName">Fully-qualified name of the function.</param>
    /// <param name="arguments">The function original arguments.</param>
    [JsonConstructor]
    public FunctionCallContent(string? id, string? pluginName, string functionName, string fullyQualifiedName, string? arguments = null)
    {
        Verify.NotNull(functionName);

        this.Id = id;
        this.PluginName = pluginName;
        this.FunctionName = functionName;
        this.FullyQualifiedName = fullyQualifiedName;
        this.Arguments = arguments;

        if (!string.IsNullOrWhiteSpace(arguments) && JsonSerializer.Deserialize<Dictionary<string, object?>>(arguments!) is { } deserializedArguments)
        {
            this.KernelArgument = new KernelArguments(deserializedArguments);
        }
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="functionName">The function name.</param>
    /// <param name="pluginName">The plugin name.</param>
    /// <param name="id">The function call ID.</param>
    /// <param name="arguments">The function original arguments.</param>
    public static FunctionCallContent Create(string functionName, string? pluginName, string? id, string? arguments = null, string functionNameSeparator = "-")
    {
        Verify.NotNull(functionName);

        return new FunctionCallContent(
            id: id,
            pluginName: pluginName,
            functionName: functionName,
            fullyQualifiedName: string.IsNullOrEmpty(pluginName) ? functionName : ($"{pluginName}{functionNameSeparator}{functionName}"),
            arguments: arguments);
    }

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionCallContent"/> class.
    /// </summary>
    /// <param name="fullyQualifiedName">Fully-qualified name of the function.</param>
    /// <param name="id">The function call ID.</param>
    /// <param name="arguments">The function original arguments.</param>
    public static FunctionCallContent Create(string fullyQualifiedName, string? id, string? arguments = null, string functionNameSeparator = "-")
    {
        Verify.NotNull(fullyQualifiedName);

        string? pluginName = null;
        string functionName = fullyQualifiedName;

        int separatorPos = fullyQualifiedName.IndexOf(functionNameSeparator, StringComparison.Ordinal);
        if (separatorPos >= 0)
        {
            pluginName = fullyQualifiedName.AsSpan(0, separatorPos).Trim().ToString();
            functionName = fullyQualifiedName.AsSpan(separatorPos + functionNameSeparator.Length).Trim().ToString();
        }

        return new FunctionCallContent(
            id: id,
            pluginName: pluginName,
            functionName: functionName,
            fullyQualifiedName: fullyQualifiedName,
            arguments: arguments);
    }

    /// <summary>
    /// Invokes the function represented by the function call content type.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function's execution.</returns>
    public Task<FunctionResult> InvokeAsync(Kernel kernel, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel, nameof(kernel));

        if (kernel.Plugins.TryGetFunctionAndArguments(this, out KernelFunction? function, out KernelArguments? arguments))
        {
            return function.InvokeAsync(kernel, arguments, cancellationToken);
        }

        throw new KeyNotFoundException($"The plugin collection does not contain a plugin and/or function with the specified names. Plugin name - '{this.PluginName}', function name - '{this.FunctionName}'.");
    }
}
