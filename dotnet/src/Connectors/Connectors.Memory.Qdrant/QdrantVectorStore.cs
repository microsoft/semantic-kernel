// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using Grpc.Core;
using Microsoft.Extensions.VectorData;
using Qdrant.Client;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Class for accessing the list of collections in a Qdrant vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public class QdrantVectorStore : IVectorStore
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    private const string DatabaseName = "Qdrant";

    /// <summary>Qdrant client that can be used to manage the collections and points in a Qdrant store.</summary>
    private readonly MockableQdrantClient _qdrantClient;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly QdrantVectorStoreOptions _options;

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorStore"/> class.
    /// </summary>
    /// <param name="qdrantClient">Qdrant client that can be used to manage the collections and points in a Qdrant store.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public QdrantVectorStore(QdrantClient qdrantClient, QdrantVectorStoreOptions? options = default)
        : this(new MockableQdrantClient(qdrantClient), options)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorStore"/> class.
    /// </summary>
    /// <param name="qdrantClient">Qdrant client that can be used to manage the collections and points in a Qdrant store.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    internal QdrantVectorStore(MockableQdrantClient qdrantClient, QdrantVectorStoreOptions? options = default)
    {
        Verify.NotNull(qdrantClient);

        this._qdrantClient = qdrantClient;
        this._options = options ?? new QdrantVectorStoreOptions();
    }

    /// <inheritdoc />
    public virtual IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
    {
#pragma warning disable CS0618 // IQdrantVectorStoreRecordCollectionFactory is obsolete
        if (this._options.VectorStoreCollectionFactory is not null)
        {
            return this._options.VectorStoreCollectionFactory.CreateVectorStoreRecordCollection<TKey, TRecord>(this._qdrantClient.QdrantClient, name, vectorStoreRecordDefinition);
        }
#pragma warning restore CS0618

        if (typeof(TKey) != typeof(ulong) && typeof(TKey) != typeof(Guid))
        {
            throw new NotSupportedException("Only ulong and Guid keys are supported.");
        }

        var recordCollection = new QdrantVectorStoreRecordCollection<TRecord>(this._qdrantClient, name, new QdrantVectorStoreRecordCollectionOptions<TRecord>()
        {
            HasNamedVectors = this._options.HasNamedVectors,
            VectorStoreRecordDefinition = vectorStoreRecordDefinition
        });
        var castRecordCollection = recordCollection as IVectorStoreRecordCollection<TKey, TRecord>;
        return castRecordCollection!;
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        IReadOnlyList<string> collections;

        try
        {
            collections = await this._qdrantClient.ListCollectionsAsync(cancellationToken).ConfigureAwait(false);
        }
        catch (RpcException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreType = DatabaseName,
                OperationName = "ListCollections"
            };
        }

        foreach (var collection in collections)
        {
            yield return collection;
        }
    }
}
