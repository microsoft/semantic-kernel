// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Class for accessing the list of collections in a Pinecone vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public sealed class PineconeVectorStore : VectorStore
{
    private readonly PineconeClient _pineconeClient;

    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreCollectionDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string)), new VectorStoreVectorProperty("Vector", typeof(ReadOnlyMemory<float>), 1)] };

    private readonly IEmbeddingGenerator? _embeddingGenerator;

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeVectorStore"/> class.
    /// </summary>
    /// <param name="pineconeClient">Pinecone client that can be used to manage the collections and points in a Pinecone store.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public PineconeVectorStore(PineconeClient pineconeClient, PineconeVectorStoreOptions? options = default)
    {
        Verify.NotNull(pineconeClient);

        this._pineconeClient = pineconeClient;
        this._embeddingGenerator = options?.EmbeddingGenerator;

        this._metadata = new()
        {
            VectorStoreSystemName = PineconeConstants.VectorStoreSystemName
        };
    }

#pragma warning disable IDE0090 // Use 'new(...)'
    /// <inheritdoc />
    [RequiresDynamicCode("This overload of GetCollection() is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, call GetDynamicCollection() instead.")]
    [RequiresUnreferencedCode("This overload of GetCollecttion() is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, call GetDynamicCollection() instead.")]
#if NET8_0_OR_GREATER
    public override PineconeCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#else
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#endif
        => typeof(TRecord) == typeof(Dictionary<string, object?>)
            ? throw new ArgumentException(VectorDataStrings.GetCollectionWithDictionaryNotSupported)
            : new PineconeCollection<TKey, TRecord>(
                this._pineconeClient,
                name,
                new PineconeCollectionOptions()
                {
                    Definition = definition,
                    EmbeddingGenerator = this._embeddingGenerator
                });

    /// <inheritdoc />
#if NET8_0_OR_GREATER
    public override PineconeDynamicCollection GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#else
    public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#endif
        => new PineconeDynamicCollection(
            this._pineconeClient,
            name,
            new()
            {
                Definition = definition,
                EmbeddingGenerator = this._embeddingGenerator
            }
        );
#pragma warning restore IDE0090

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
        var collection = this.GetDynamicCollection(name, s_generalPurposeDefinition);
        return collection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override Task EnsureCollectionDeletedAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetDynamicCollection(name, s_generalPurposeDefinition);
        return collection.EnsureCollectionDeletedAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreMetadata) ? this._metadata :
            serviceType == typeof(PineconeClient) ? this._pineconeClient :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
