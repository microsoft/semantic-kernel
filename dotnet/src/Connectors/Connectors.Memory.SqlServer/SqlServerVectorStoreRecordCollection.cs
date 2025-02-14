// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal sealed class SqlServerVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>
    where TKey : notnull
{
    private readonly SqlConnection _sqlConnection;
    private readonly SqlServerVectorStoreOptions _options;
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    internal SqlServerVectorStoreRecordCollection(SqlConnection sqlConnection, string name, SqlServerVectorStoreOptions options, VectorStoreRecordPropertyReader propertyReader)
    {
        this._sqlConnection = sqlConnection;
        this.CollectionName = name;
        this._options = options;
        this._propertyReader = propertyReader;
    }

    public string CollectionName { get; }

    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        await this.EnsureConnectionIsOpenedAsync(cancellationToken).ConfigureAwait(false);

        using SqlCommand command = SqlServerCommandBuilder.SelectTableName(this._sqlConnection, this._options.Schema, this.CollectionName);
        using SqlDataReader reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        return await reader.ReadAsync(cancellationToken).ConfigureAwait(false);
    }

    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
        => this.CreateCollectionAsync(ifNotExists: false, cancellationToken);

    // TODO adsitnik: design: We typically don't provide such methods in BCL.
    // 1. I totally see why we want to provide it, we just need to make sure it's the right thing to do.
    // 2. An alternative would be to make CreateCollectionAsync a nop when the collection already exists
    // or extend it with an optional boolan parameter that would control the behavior.
    public Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
        => this.CreateCollectionAsync(ifNotExists: true, cancellationToken);

    private async Task CreateCollectionAsync(bool ifNotExists, CancellationToken cancellationToken)
    {
        await this.EnsureConnectionIsOpenedAsync(cancellationToken).ConfigureAwait(false);

        using SqlCommand command = SqlServerCommandBuilder.CreateTable(
            this._sqlConnection,
            this._options,
            this.CollectionName,
            ifNotExists,
            this._propertyReader.KeyProperty,
            this._propertyReader.DataProperties,
            this._propertyReader.VectorProperties);

        await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    public async Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        await this.EnsureConnectionIsOpenedAsync(cancellationToken).ConfigureAwait(false);

        using SqlCommand cmd = SqlServerCommandBuilder.DropTable(this._sqlConnection, this._options.Schema, this.CollectionName);

        await cmd.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    private Task EnsureConnectionIsOpenedAsync(CancellationToken cancellationToken)
        => this._sqlConnection.State == System.Data.ConnectionState.Open
            ? Task.CompletedTask
            : this._sqlConnection.OpenAsync(cancellationToken);

    public Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    public Task DeleteBatchAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    public Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    public IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    public Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    public IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    public Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }
}
