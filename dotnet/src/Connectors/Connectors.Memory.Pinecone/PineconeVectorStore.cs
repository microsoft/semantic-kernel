// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Pinecone;
using Sdk = Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Class for accessing the list of collections in a Pinecone vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public sealed class PineconeVectorStore : VectorStore
{
    private readonly Sdk.PineconeClient _pineconeClient;
    private readonly PineconeVectorStoreOptions _options;

    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreRecordDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string)), new VectorStoreVectorProperty("Vector", typeof(ReadOnlyMemory<float>), 1)] };

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeVectorStore"/> class.
    /// </summary>
    /// <param name="pineconeClient">Pinecone client that can be used to manage the collections and points in a Pinecone store.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public PineconeVectorStore(Sdk.PineconeClient pineconeClient, PineconeVectorStoreOptions? options = default)
    {
        Verify.NotNull(pineconeClient);

        this._pineconeClient = pineconeClient;
        this._options = options ?? new PineconeVectorStoreOptions();

        this._metadata = new()
        {
            VectorStoreSystemName = PineconeConstants.VectorStoreSystemName
        };
    }

    /// <inheritdoc />
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        => (new PineconeCollection<TKey, TRecord>(
            this._pineconeClient,
            name,
            new PineconeCollectionOptions<TRecord>()
            {
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                EmbeddingGenerator = this._options.EmbeddingGenerator
            }) as VectorStoreCollection<TKey, TRecord>)!;

    /// <inheritdoc />
    public override async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var indexList = await VectorStoreErrorHandler.RunOperationAsync<IndexList, PineconeApiException>(
            this._metadata,
            "ListCollections",
            () => this._pineconeClient.ListIndexesAsync(cancellationToken: cancellationToken)).ConfigureAwait(false);

        if (indexList.Indexes is not null)
        {
            foreach (var index in indexList.Indexes)
            {
                yield return index.Name;
            }
        }
    }

    /// <inheritdoc />
    public override Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.DeleteCollectionAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreMetadata) ? this._metadata :
            serviceType == typeof(Sdk.PineconeClient) ? this._pineconeClient :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
