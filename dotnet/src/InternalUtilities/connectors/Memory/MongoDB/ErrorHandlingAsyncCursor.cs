// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using MongoDB.Driver;

/// <summary>
/// A decorator for <see cref="IAsyncCursor{T}"/> that handles errors on move next.
/// </summary>
/// <typeparam name="T">The type that the cursor returns.</typeparam>
internal class ErrorHandlingAsyncCursor<T> : IAsyncCursor<T>
{
    private readonly IAsyncCursor<T> _cursor;
    private readonly string _operationName;
    private readonly VectorStoreRecordCollectionMetadata _collectionMetadata;

    public ErrorHandlingAsyncCursor(IAsyncCursor<T> cursor, VectorStoreRecordCollectionMetadata collectionMetadata, string operationName)
    {
        this._cursor = cursor;
        this._operationName = operationName;
        this._collectionMetadata = collectionMetadata;
    }

    public ErrorHandlingAsyncCursor(IAsyncCursor<T> cursor, VectorStoreMetadata metadata, string operationName)
    {
        this._cursor = cursor;
        this._operationName = operationName;
        this._collectionMetadata = new VectorStoreRecordCollectionMetadata()
        {
            CollectionName = null,
            VectorStoreName = metadata.VectorStoreName,
            VectorStoreSystemName = metadata.VectorStoreSystemName,
        };
    }

    public IEnumerable<T> Current => this._cursor.Current;

    public void Dispose()
    {
        this._cursor.Dispose();
    }

    public bool MoveNext(CancellationToken cancellationToken = default)
    {
        return VectorStoreErrorHandler.RunOperation<bool, MongoException>(
            this._collectionMetadata,
            this._operationName,
            () => this._cursor.MoveNext(cancellationToken));
    }

    public Task<bool> MoveNextAsync(CancellationToken cancellationToken = default)
    {
        return VectorStoreErrorHandler.RunOperationAsync<bool, MongoException>(
            this._collectionMetadata,
            this._operationName,
            () => this._cursor.MoveNextAsync(cancellationToken));
    }
}
