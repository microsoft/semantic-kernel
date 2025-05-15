﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using MongoDB.Driver;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Class for accessing the list of collections in a MongoDB vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public sealed class MongoVectorStore : VectorStore
{
    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary><see cref="IMongoDatabase"/> that can be used to manage the collections in MongoDB.</summary>
    private readonly IMongoDatabase _mongoDatabase;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreRecordDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string))] };

    private readonly IEmbeddingGenerator? _embeddingGenerator;

    /// <summary>
    /// Initializes a new instance of the <see cref="MongoVectorStore"/> class.
    /// </summary>
    /// <param name="mongoDatabase"><see cref="IMongoDatabase"/> that can be used to manage the collections in MongoDB.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public MongoVectorStore(IMongoDatabase mongoDatabase, MongoVectorStoreOptions? options = default)
    {
        Verify.NotNull(mongoDatabase);

        this._mongoDatabase = mongoDatabase;
        this._embeddingGenerator = options?.EmbeddingGenerator;

        this._metadata = new()
        {
            VectorStoreSystemName = MongoConstants.VectorStoreSystemName,
            VectorStoreName = mongoDatabase.DatabaseNamespace?.DatabaseName
        };
    }

#pragma warning disable IDE0090 // Use 'new(...)'
    /// <inheritdoc />
    [RequiresDynamicCode("This overload of GetCollection() is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, call GetDynamicCollection() instead.")]
    [RequiresUnreferencedCode("This overload of GetCollecttion() is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, call GetDynamicCollection() instead.")]
#if NET8_0_OR_GREATER
    public override MongoCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
#else
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
#endif
        => typeof(TRecord) == typeof(Dictionary<string, object?>)
            ? throw new ArgumentException(VectorDataStrings.GetCollectionWithDictionaryNotSupported)
            : new MongoCollection<TKey, TRecord>(
                this._mongoDatabase,
                name,
                new()
                {
                    Definition = vectorStoreRecordDefinition,
                    EmbeddingGenerator = this._embeddingGenerator
                });

    /// <inheritdoc />
#if NET8_0_OR_GREATER
    public override MongoDynamicCollection GetDynamicCollection(string name, VectorStoreRecordDefinition vectorStoreRecordDefinition)
#else
    public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(string name, VectorStoreRecordDefinition vectorStoreRecordDefinition)
#endif
        => new MongoDynamicCollection(
            this._mongoDatabase,
            name,
            new()
            {
                Definition = vectorStoreRecordDefinition,
                EmbeddingGenerator = this._embeddingGenerator,
            }
        );
#pragma warning restore IDE0090

    /// <inheritdoc />
    public override async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "ListCollectionNames";

        using var cursor = await VectorStoreErrorHandler.RunOperationAsync<IAsyncCursor<string>, MongoException>(
            this._metadata,
            OperationName,
            () => this._mongoDatabase.ListCollectionNamesAsync(cancellationToken: cancellationToken)).ConfigureAwait(false);
        using var errorHandlingAsyncCursor = new ErrorHandlingAsyncCursor<string>(cursor, this._metadata, OperationName);

        while (await cursor.MoveNextAsync(cancellationToken).ConfigureAwait(false))
        {
            foreach (var name in cursor.Current)
            {
                yield return name;
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
    public override Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetDynamicCollection(name, s_generalPurposeDefinition);
        return collection.DeleteCollectionAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
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
