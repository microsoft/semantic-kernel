// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Function result after execution.
/// </summary>
public sealed class StreamingFunctionResult : IAsyncEnumerable<StreamingResultChunk>
{
    internal Dictionary<string, object>? _metadata;
    private readonly IAsyncEnumerable<StreamingResultChunk> _streamingResult;

    /// <summary>
    /// Name of executed function.
    /// </summary>
    public string FunctionName { get; internal set; }

    /// <summary>
    /// Name of the plugin containing the function.
    /// </summary>
    public string PluginName { get; internal set; }

    /// <summary>
    /// Metadata for storing additional information about function execution result.
    /// </summary>
    public Dictionary<string, object> Metadata
    {
        get => this._metadata ??= new();
        internal set => this._metadata = value;
    }

    /// <summary>
    /// Internal object reference. (Breaking glass).
    /// Each connector will have its own internal object representing the result.
    /// </summary>
    /// <remarks>
    /// The usage of this property is considered "unsafe". Use it only if strictly necessary.
    /// </remarks>
    public object? InnerFunctionResult { get; private set; } = null;

    /// <summary>
    /// Instance of <see cref="SKContext"/> used by the function.
    /// </summary>
    internal SKContext Context { get; private set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionResult"/> class.
    /// </summary>
    /// <param name="functionName">Name of executed function.</param>
    /// <param name="pluginName">Name of the plugin containing the function.</param>
    /// <param name="context">Instance of <see cref="SKContext"/> to pass in function pipeline.</param>
    /// <param name="streamingResult">IAsyncEnumerable reference to iterate</param>
    /// <param name="innerFunctionResult">Inner function result object reference</param>
    public StreamingFunctionResult(string functionName, string pluginName, SKContext context, IAsyncEnumerable<StreamingResultChunk> streamingResult, object? innerFunctionResult)
    {
        this.FunctionName = functionName;
        this.PluginName = pluginName;
        this.Context = context;
        this._streamingResult = streamingResult;
        this.InnerFunctionResult = innerFunctionResult;
    }

    /// <summary>
    /// Get typed value from metadata.
    /// </summary>
    public bool TryGetMetadataValue<T>(string key, out T value)
    {
        if (this._metadata is { } metadata &&
            metadata.TryGetValue(key, out object? valueObject) &&
            valueObject is T typedValue)
        {
            value = typedValue;
            return true;
        }

        value = default!;
        return false;
    }

    /// <summary>
    /// Get the enumerator for the streaming result.
    /// </summary>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>Streaming chunk asynchronous enumerator</returns>
    public IAsyncEnumerator<StreamingResultChunk> GetAsyncEnumerator(CancellationToken cancellationToken = default)
        => this._streamingResult.GetAsyncEnumerator(cancellationToken);
}
