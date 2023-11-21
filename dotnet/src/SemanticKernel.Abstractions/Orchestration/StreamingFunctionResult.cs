// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Function result after execution.
/// </summary>
public sealed class StreamingFunctionResult<T> : IAsyncEnumerable<T>
{
    internal Dictionary<string, object>? _metadata;
    private readonly IAsyncEnumerable<T> _streamingResult;

    /// <summary>
    /// Name of executed function.
    /// </summary>
    public string FunctionName { get; internal set; }

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
    public object? InnerResult { get; private set; } = null;

    /// <summary>
    /// Instance of <see cref="SKContext"/> used by the function.
    /// </summary>
    internal SKContext Context { get; private set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionResult"/> class.
    /// </summary>
    /// <param name="functionName">Name of executed function.</param>
    /// <param name="context">Instance of <see cref="SKContext"/> to pass in function pipeline.</param>
    /// <param name="streamingResult">IAsyncEnumerable reference to iterate</param>
    /// <param name="innerFunctionResult">Inner function result object reference</param>
    public StreamingFunctionResult(string functionName, SKContext context, Func<IAsyncEnumerable<T>> streamingResult, object? innerFunctionResult)
    {
        this.FunctionName = functionName;
        this.Context = context;
        this._streamingResult = streamingResult.Invoke();
        this.InnerResult = innerFunctionResult;
    }

    /// <summary>
    /// Get typed value from metadata.
    /// </summary>
    public bool TryGetMetadataValue<TValue>(string key, out TValue value)
    {
        if (this._metadata is { } metadata &&
            metadata.TryGetValue(key, out object? valueObject) &&
            valueObject is TValue typedValue)
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
    public IAsyncEnumerator<T> GetAsyncEnumerator(CancellationToken cancellationToken = default)
        => (IAsyncEnumerator<T>)this._streamingResult.GetAsyncEnumerator(cancellationToken);
}

/// <summary>
/// Connector Async Enumerable Reuslt
/// </summary>
/// <typeparam name="T"></typeparam>
public sealed class ConnectorAsyncEnumerable<T> : IAsyncEnumerable<T>
{
    private readonly IAsyncEnumerable<T> _streamingResultSource;

    /// <summary>
    /// Internal object reference. (Breaking glass).
    /// Each connector will have its own internal object representing the result.
    /// </summary>
    /// <remarks>
    /// The usage of this property is considered "unsafe". Use it only if strictly necessary.
    /// </remarks>
    public object? InnerResult { get; private set; } = null;

    internal Dictionary<string, object>? _metadata;

    /// <summary>
    /// Metadata for storing additional information about function execution result.
    /// </summary>
    public Dictionary<string, object> Metadata
    {
        get => this._metadata ??= new();
        internal set => this._metadata = value;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ConnectorAsyncEnumerable{T}"/> class.
    /// </summary>
    /// <param name="streamingReference"></param>
    /// <param name="innerConnectorResult"></param>
    public ConnectorAsyncEnumerable(Func<IAsyncEnumerable<T>> streamingReference, object? innerConnectorResult)
    {
        this._streamingResultSource = streamingReference.Invoke();
        this.InnerResult = innerConnectorResult;
    }

    /// <inheritdoc/>
    public IAsyncEnumerator<T> GetAsyncEnumerator(CancellationToken cancellationToken = default)
    {
        return this._streamingResultSource.GetAsyncEnumerator(cancellationToken);
    }
}
