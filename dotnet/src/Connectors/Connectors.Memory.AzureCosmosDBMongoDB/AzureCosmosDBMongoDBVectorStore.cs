// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
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
    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary><see cref="IMongoDatabase"/> that can be used to manage the collections in Azure CosmosDB MongoDB.</summary>
    private readonly IMongoDatabase _mongoDatabase;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly AzureCosmosDBMongoDBVectorStoreOptions _options;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreRecordDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreRecordKeyProperty("Key", typeof(string))] };

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

        this._metadata = new()
        {
            VectorStoreSystemName = AzureCosmosDBMongoDBConstants.VectorStoreSystemName,
            VectorStoreName = mongoDatabase.DatabaseNamespace?.DatabaseName
        };
    }

    /// <inheritdoc />
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
        where TRecord : notnull
    {
#pragma warning disable CS0618 // IAzureCosmosDBMongoDBVectorStoreRecordCollectionFactory is obsolete
        if (this._options.VectorStoreCollectionFactory is not null)
        {
            return this._options.VectorStoreCollectionFactory.CreateVectorStoreRecordCollection<TKey, TRecord>(this._mongoDatabase, name, vectorStoreRecordDefinition);
        }
#pragma warning restore CS0618

        var recordCollection = new AzureCosmosDBMongoDBVectorStoreRecordCollection<TKey, TRecord>(
            this._mongoDatabase,
            name,
            new()
            {
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                EmbeddingGenerator = this._options.EmbeddingGenerator
            }) as IVectorStoreRecordCollection<TKey, TRecord>;

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

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.DeleteCollectionAsync(cancellationToken);
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreMetadata) ? this._metadata :
            serviceType == typeof(IMongoDatabase) ? this._mongoDatabase :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
