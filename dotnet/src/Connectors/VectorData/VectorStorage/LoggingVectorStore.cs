// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// A vector store that logs operations to an <see cref="ILogger"/>
/// </summary>
[Experimental("SKEXP0020")]
public class LoggingVectorStore : IVectorStore
{
    /// <summary>An <see cref="ILogger"/> instance used for all logging.</summary>
    private readonly ILogger _logger;

    /// <summary>The underlying <see cref="IVectorStore"/>.</summary>
    private readonly IVectorStore _innerStore;

    /// <summary>
    /// Initializes a new instance of the <see cref="LoggingVectorStore"/> class.
    /// </summary>
    /// <param name="innerStore">The underlying <see cref="IVectorStore"/>.</param>
    /// <param name="logger">An <see cref="ILogger"/> instance that will be used for all logging.</param>
    public LoggingVectorStore(IVectorStore innerStore, ILogger logger)
    {
        Verify.NotNull(innerStore);
        Verify.NotNull(logger);

        this._innerStore = innerStore;
        this._logger = logger;
    }

    /// <inheritdoc/>
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null) where TKey : notnull
        => new LoggingVectorStoreRecordCollection<TKey, TRecord>(
            this._innerStore.GetCollection<TKey, TRecord>(name, vectorStoreRecordDefinition),
            this._logger);

    /// <inheritdoc/>
    public IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default)
    {
        return LoggingExtensions.RunWithLoggingAsync(
            this._logger,
            nameof(ListCollectionNamesAsync),
            () => this._innerStore.ListCollectionNamesAsync(cancellationToken),
            cancellationToken);
    }

    /// <inheritdoc/>
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is null && serviceType.IsInstanceOfType(this) ? this :
            this._innerStore.GetService(serviceType, serviceKey);
    }
}
