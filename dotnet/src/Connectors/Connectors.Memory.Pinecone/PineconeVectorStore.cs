// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
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
public class PineconeVectorStore : IVectorStore
{
    private const string DatabaseName = "Pinecone";

    private readonly Sdk.PineconeClient _pineconeClient;
    private readonly PineconeVectorStoreOptions _options;

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
    }

    /// <inheritdoc />
    public virtual IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
    {
#pragma warning disable CS0618 // IPineconeVectorStoreRecordCollectionFactory is obsolete
        if (this._options.VectorStoreCollectionFactory is not null)
        {
            return this._options.VectorStoreCollectionFactory.CreateVectorStoreRecordCollection<TKey, TRecord>(this._pineconeClient, name, vectorStoreRecordDefinition);
        }
#pragma warning restore CS0618

        if (typeof(TKey) != typeof(string))
        {
            throw new NotSupportedException("Only string keys are supported.");
        }

        return (new PineconeVectorStoreRecordCollection<TRecord>(
            this._pineconeClient,
            name,
            new PineconeVectorStoreRecordCollectionOptions<TRecord>() { VectorStoreRecordDefinition = vectorStoreRecordDefinition }) as IVectorStoreRecordCollection<TKey, TRecord>)!;
    }

    /// <inheritdoc />
    public virtual async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        IndexList indexList;

        try
        {
            indexList = await this._pineconeClient.ListIndexesAsync(cancellationToken: cancellationToken).ConfigureAwait(false);
        }
        catch (PineconeApiException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreType = DatabaseName,
                OperationName = "ListCollections"
            };
        }

        if (indexList.Indexes is not null)
        {
            foreach (var index in indexList.Indexes)
            {
                yield return index.Name;
            }
        }
    }
}
