﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Class for accessing the list of collections in a Azure CosmosDB NoSQL vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public sealed class CosmosNoSqlVectorStore : VectorStore
{
    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary><see cref="Database"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</summary>
    private readonly Database _database;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly CosmosNoSqlVectorStoreOptions _options;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreRecordDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string))] };

    /// <summary>
    /// Initializes a new instance of the <see cref="CosmosNoSqlVectorStore"/> class.
    /// </summary>
    /// <param name="database"><see cref="Database"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public CosmosNoSqlVectorStore(Database database, CosmosNoSqlVectorStoreOptions? options = null)
    {
        Verify.NotNull(database);

        this._database = database;
        this._options = options ?? new();

        this._metadata = new()
        {
            VectorStoreSystemName = CosmosNoSqlConstants.VectorStoreSystemName,
            VectorStoreName = database.Id
        };
    }

#pragma warning disable IDE0090 // Use 'new(...)'
    /// <inheritdoc />
#if NET8_0_OR_GREATER
    public override CosmosNoSqlCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
#else
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
#endif
        => new CosmosNoSqlCollection<TKey, TRecord>(
            this._database,
            name,
            new()
            {
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                JsonSerializerOptions = this._options.JsonSerializerOptions,
                EmbeddingGenerator = this._options.EmbeddingGenerator
            });
#pragma warning restore IDE0090

    /// <inheritdoc />
    public override async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string Query = "SELECT VALUE(c.id) FROM c";

        const string OperationName = "ListCollectionNamesAsync";
        using var feedIterator = VectorStoreErrorHandler.RunOperation<FeedIterator<string>, CosmosException>(
            this._metadata,
            OperationName,
            () => this._database.GetContainerQueryIterator<string>(Query));
        using var errorHandlingFeedIterator = new ErrorHandlingFeedIterator<string>(feedIterator, this._metadata, OperationName);

        while (feedIterator.HasMoreResults)
        {
            var next = await feedIterator.ReadNextAsync(cancellationToken).ConfigureAwait(false);

            foreach (var containerName in next.Resource)
            {
                yield return containerName;
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
            serviceType == typeof(Database) ? this._database :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
