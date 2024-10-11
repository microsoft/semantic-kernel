﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using Microsoft.Extensions.VectorData;
using MongoDB.Driver;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Class for accessing the list of collections in a Azure CosmosDB MongoDB vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public sealed class AzureCosmosDBMongoDBVectorStore : IVectorStore
{
    /// <summary><see cref="IMongoDatabase"/> that can be used to manage the collections in Azure CosmosDB MongoDB.</summary>
    private readonly IMongoDatabase _mongoDatabase;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly AzureCosmosDBMongoDBVectorStoreOptions _options;

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureCosmosDBMongoDBVectorStore"/> class.
    /// </summary>
    /// <param name="mongoDatabase"><see cref="IMongoDatabase"/> that can be used to manage the collections in Azure CosmosDB MongoDB.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public AzureCosmosDBMongoDBVectorStore(IMongoDatabase mongoDatabase, AzureCosmosDBMongoDBVectorStoreOptions? options = default)
    {
        Verify.NotNull(mongoDatabase);

        this._mongoDatabase = mongoDatabase;
        this._options = options ?? new();
    }

    /// <inheritdoc />
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
        where TRecord : class
    {
        if (typeof(TKey) != typeof(string))
        {
            throw new NotSupportedException("Only string keys are supported.");
        }

        if (this._options.VectorStoreCollectionFactory is not null)
        {
            return this._options.VectorStoreCollectionFactory.CreateVectorStoreRecordCollection<TKey, TRecord>(this._mongoDatabase, name, vectorStoreRecordDefinition);
        }

        var recordCollection = new AzureCosmosDBMongoDBVectorStoreRecordCollection<TRecord>(
            this._mongoDatabase,
            name,
            new() { VectorStoreRecordDefinition = vectorStoreRecordDefinition }) as IVectorStoreRecordCollection<TKey, TRecord>;

        return recordCollection!;
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var cursor = await this._mongoDatabase
            .ListCollectionNamesAsync(cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var name in cursor.Current)
            {
                yield return name;
            }
        }
    }
}
