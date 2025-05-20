// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

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

    private readonly ClientWrapper _clientWrapper;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreCollectionDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string))] };

    private readonly JsonSerializerOptions? _jsonSerializerOptions;
    private readonly IEmbeddingGenerator? _embeddingGenerator;

    /// <summary>
    /// Initializes a new instance of the <see cref="CosmosNoSqlVectorStore"/> class.
    /// </summary>
    /// <param name="database"><see cref="Database"/> that can be used to manage the collections in Azure CosmosDB NoSQL.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [RequiresUnreferencedCode("The Cosmos NoSQL provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Cosmos NoSQL provider is currently incompatible with NativeAOT.")]
    public CosmosNoSqlVectorStore(Database database, CosmosNoSqlVectorStoreOptions? options = null)
        : this(new(database.Client, ownsClient: false), _ => database, options)
    {
        Verify.NotNull(database);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="CosmosNoSqlVectorStore"/> class.
    /// </summary>
    /// <param name="connectionString">Connection string required to connect to Azure CosmosDB NoSQL.</param>
    /// <param name="databaseName">Database name for Azure CosmosDB NoSQL.</param>
    /// <param name="clientOptions">Optional configuration options for <see cref="CosmosClient"/>.</param>
    /// <param name="storeOptions">Optional configuration options for <see cref="VectorStore"/>.</param>
    public CosmosNoSqlVectorStore(string connectionString, string databaseName,
        CosmosClientOptions? clientOptions = null, CosmosNoSqlVectorStoreOptions? storeOptions = null)
        : this(new ClientWrapper(new CosmosClient(connectionString, clientOptions), ownsClient: true), client => client.GetDatabase(databaseName), storeOptions)
    {
        Verify.NotNullOrWhiteSpace(connectionString);
        Verify.NotNullOrWhiteSpace(databaseName);
    }

    private CosmosNoSqlVectorStore(ClientWrapper clientWrapper,
        Func<CosmosClient, Database> databaseProvider, CosmosNoSqlVectorStoreOptions? options)
    {
        try
        {
            this._database = databaseProvider(clientWrapper.Client);
            this._embeddingGenerator = options?.EmbeddingGenerator;
            this._jsonSerializerOptions = options?.JsonSerializerOptions;

            this._metadata = new()
            {
                VectorStoreSystemName = CosmosNoSqlConstants.VectorStoreSystemName,
                VectorStoreName = this._database.Id
            };
        }
        catch (Exception)
        {
            // Something went wrong, we dispose the client and don't store a reference.
            clientWrapper.Dispose();

            throw;
        }

        this._clientWrapper = clientWrapper;
    }

    /// <inheritdoc/>
    protected override void Dispose(bool disposing)
    {
        this._clientWrapper.Dispose();
        base.Dispose(disposing);
    }

#pragma warning disable IDE0090 // Use 'new(...)'
    /// <inheritdoc />
    [RequiresUnreferencedCode("The Cosmos NoSQL provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Cosmos NoSQL provider is currently incompatible with NativeAOT.")]
#if NET8_0_OR_GREATER
    public override CosmosNoSqlCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#else
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#endif
        => typeof(TRecord) == typeof(Dictionary<string, object?>)
            ? throw new ArgumentException(VectorDataStrings.GetCollectionWithDictionaryNotSupported)
            : new CosmosNoSqlCollection<TKey, TRecord>(
                this._clientWrapper.Share(),
                _ => this._database,
                name,
                new()
                {
                    Definition = definition,
                    JsonSerializerOptions = this._jsonSerializerOptions,
                    EmbeddingGenerator = this._embeddingGenerator
                });

    /// <inheritdoc />
    [RequiresUnreferencedCode("The Cosmos NoSQL provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Cosmos NoSQL provider is currently incompatible with NativeAOT.")]
#if NET8_0_OR_GREATER
    public override CosmosNoSqlDynamicCollection GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#else
    public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#endif
        => new CosmosNoSqlDynamicCollection(
            this._clientWrapper.Share(),
            _ => this._database,
            name,
            new()
            {
                Definition = definition,
                JsonSerializerOptions = this._jsonSerializerOptions,
                EmbeddingGenerator = this._embeddingGenerator
            }
        );
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
            serviceType == typeof(Database) ? this._database :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
