// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Provides an optional base class for an <see cref="IVectorStore"/> that passes through calls to another instance.
/// </summary>
/// <remarks>
/// This is recommended as a base type when building services that can be chained around an underlying <see cref="IVectorStore"/>.
/// The default implementation simply passes each call to the inner client instance.
/// </remarks>
[Experimental("SKEXP0020")]
public class DelegatingVectorStore : IVectorStore
{
    /// <summary>Gets the inner <see cref="IVectorStore"/>.</summary>
    protected IVectorStore InnerStore { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="DelegatingVectorStore"/> class.
    /// </summary>
    /// <param name="vectorStore">The wrapped store instance.</param>
    protected DelegatingVectorStore(IVectorStore vectorStore)
    {
        this.InnerStore = vectorStore ?? throw new ArgumentNullException(nameof(vectorStore));
    }

    /// <inheritdoc />
    public virtual IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null) where TKey : notnull
    {
        return this.InnerStore.GetCollection<TKey, TRecord>(name, vectorStoreRecordDefinition);
    }

    /// <inheritdoc />
    public virtual IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default)
    {
        return this.InnerStore.ListCollectionNamesAsync(cancellationToken);
    }
}
