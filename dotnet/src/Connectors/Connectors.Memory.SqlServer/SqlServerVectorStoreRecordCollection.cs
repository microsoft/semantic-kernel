// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
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

        using SqlCommand command = SqlServerCommandBuilder.SelectTableName(
            this._sqlConnection, this._options.Schema, this.CollectionName);
        using SqlDataReader reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

        return await reader.ReadAsync(cancellationToken).ConfigureAwait(false);
    }

    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
        => this.CreateCollectionAsync(ifNotExists: false, cancellationToken);

    // TODO adsitnik: design: We typically don't provide such methods in BCL.
    // 1. I totally see why we want to provide it, we just need to make sure it's the right thing to do.
    // 2. An alternative would be to make CreateCollectionAsync a nop when the collection already exists
    // or extend it with an optional boolean parameter that would control the behavior.
    // 3. We may need it to avoid TOCTOU issues.
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

        using SqlCommand command = SqlServerCommandBuilder.DropTableIfExists(
            this._sqlConnection, this._options.Schema, this.CollectionName);

        await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    public async Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        await this.EnsureConnectionIsOpenedAsync(cancellationToken).ConfigureAwait(false);

        using SqlCommand command = SqlServerCommandBuilder.DeleteSingle(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            key);

        await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    public async Task DeleteBatchAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        await this.EnsureConnectionIsOpenedAsync(cancellationToken).ConfigureAwait(false);

        using SqlCommand command = SqlServerCommandBuilder.DeleteMany(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            keys);

        await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    public async Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        await this.EnsureConnectionIsOpenedAsync(cancellationToken).ConfigureAwait(false);

        using SqlCommand command = SqlServerCommandBuilder.SelectSingle(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            key);

        using SqlDataReader reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

        return await reader.ReadAsync(cancellationToken).ConfigureAwait(false)
            ? Map(reader, this._propertyReader)
            : default;
    }

    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        await this.EnsureConnectionIsOpenedAsync(cancellationToken).ConfigureAwait(false);

        using SqlCommand command = SqlServerCommandBuilder.SelectMany(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            keys);

        using SqlDataReader reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return Map(reader, this._propertyReader);
        }
    }

    public async Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        await this.EnsureConnectionIsOpenedAsync(cancellationToken).ConfigureAwait(false);

        TKey? key = (TKey)this._propertyReader.KeyPropertyInfo.GetValue(record);
        Dictionary<string, object?> map = Map(record, this._propertyReader);

        if (key is null || key.Equals(default(TKey)))
        {
            // When the key was not provided, we are inserting a new record.
            using SqlCommand insertCommand = SqlServerCommandBuilder.InsertInto(
                this._sqlConnection,
                this._options,
                this.CollectionName,
                this._propertyReader.KeyProperty,
                this._propertyReader.DataProperties,
                this._propertyReader.VectorProperties,
                map);

            using SqlDataReader reader = await insertCommand.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
            await reader.ReadAsync(cancellationToken).ConfigureAwait(false);
            return reader.GetFieldValue<TKey>(0);
        }

        using SqlCommand command = SqlServerCommandBuilder.MergeIntoSingle(
            this._sqlConnection,
            this._options,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            map);

        await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
        return key;
    }

    public async IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        await this.EnsureConnectionIsOpenedAsync(cancellationToken).ConfigureAwait(false);

        using SqlCommand command = SqlServerCommandBuilder.MergeIntoMany(
            this._sqlConnection,
            this._options,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            records.Select(record => Map(record, this._propertyReader)));

        using SqlDataReader reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return reader.GetFieldValue<TKey>(0);
        }
    }

    public Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        throw new NotImplementedException();
    }

    private Task EnsureConnectionIsOpenedAsync(CancellationToken cancellationToken)
        => this._sqlConnection.State == System.Data.ConnectionState.Open
            ? Task.CompletedTask
            : this._sqlConnection.OpenAsync(cancellationToken);

    private static Dictionary<string, object?> Map(TRecord record, VectorStoreRecordPropertyReader propertyReader)
    {
        Dictionary<string, object?> map = new(StringComparer.Ordinal);
        map[propertyReader.KeyProperty.DataModelPropertyName] = propertyReader.KeyPropertyInfo.GetValue(record);

        var dataProperties = propertyReader.DataProperties;
        for (int i = 0; i < dataProperties.Count; i++)
        {
            object value = propertyReader.DataPropertiesInfo[i].GetValue(record);
            // SQL Server does not support arrays, so we need to serialize them to JSON.
            object? mappedValue = value switch
            {
                string[] array => JsonSerializer.Serialize(array),
                List<string> list => JsonSerializer.Serialize(list),
                _ => value
            };

            map[dataProperties[i].DataModelPropertyName] = mappedValue;
        }
        var vectorProperties = propertyReader.VectorProperties;
        for (int i = 0; i < vectorProperties.Count; i++)
        {
            // We restrict the vector properties to ReadOnlyMemory<float> so the cast here is safe.
            ReadOnlyMemory<float> floats = (ReadOnlyMemory<float>)propertyReader.VectorPropertiesInfo[i].GetValue(record);
            // We know that SqlServer supports JSON serialization, so we can serialize the vector as JSON now,
            // so the SqlServerCommandBuilder does not need to worry about that.
            // TODO adsitnik perf: we could remove the dependency to System.Text.Json
            // by using a hand-written serializer.
            map[vectorProperties[i].DataModelPropertyName] = JsonSerializer.Serialize(floats);
        }

        return map;
    }

    private static TRecord Map(SqlDataReader reader, VectorStoreRecordPropertyReader propertyReader)
    {
        TRecord record = Activator.CreateInstance<TRecord>()!;
        propertyReader.KeyPropertyInfo.SetValue(record, reader[SqlServerCommandBuilder.GetColumnName(propertyReader.KeyProperty)]);
        var data = propertyReader.DataProperties;
        var dataInfo = propertyReader.DataPropertiesInfo;
        for (int i = 0; i < data.Count; i++)
        {
            object value = reader[SqlServerCommandBuilder.GetColumnName(data[i])];
            if (value is DBNull)
            {
                // There is no need to call the reflection to set the null,
                // as it's the default value of every .NET reference type field.
                continue;
            }

            if (value is not string text)
            {
                dataInfo[i].SetValue(record, value);
            }
            else
            {
                // SQL Server does not support arrays, so we need to deserialize them from JSON.
                object? mappedValue = data[i].PropertyType switch
                {
                    Type t when t == typeof(string[]) => JsonSerializer.Deserialize<string[]>(text),
                    Type t when t == typeof(List<string>) => JsonSerializer.Deserialize<List<string>>(text),
                    _ => text
                };
                dataInfo[i].SetValue(record, mappedValue);
            }
        }

        var vector = propertyReader.VectorProperties;
        var vectorInfo = propertyReader.VectorPropertiesInfo;
        for (int i = 0; i < vector.Count; i++)
        {
            object value = reader[SqlServerCommandBuilder.GetColumnName(vector[i])];
            if (value is not DBNull)
            {
                // We know that it has to be a ReadOnlyMemory<float> because that's what we serialized.
                ReadOnlyMemory<float> embedding = JsonSerializer.Deserialize<ReadOnlyMemory<float>>((string)value);
                vectorInfo[i].SetValue(record, embedding);
            }
        }
        return record;
    }
}
