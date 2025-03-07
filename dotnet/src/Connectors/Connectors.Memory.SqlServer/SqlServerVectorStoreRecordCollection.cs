// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// An implementation of <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> backed by a SQL Server or Azure SQL database.
/// </summary>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix (Collection)
public sealed class SqlServerVectorStoreRecordCollection<TKey, TRecord>
#pragma warning restore CA1711
    : IVectorStoreRecordCollection<TKey, TRecord> where TKey : notnull
{
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();
    private static readonly SqlServerVectorStoreRecordCollectionOptions<TRecord> s_defaultOptions = new();

    private readonly SqlConnection _sqlConnection;
    private readonly SqlServerVectorStoreRecordCollectionOptions<TRecord> _options;
    private readonly VectorStoreRecordPropertyReader _propertyReader;
    private readonly IVectorStoreRecordMapper<TRecord, IDictionary<string, object?>> _mapper;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="connection">Database connection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options.</param>
    public SqlServerVectorStoreRecordCollection(
        SqlConnection connection,
        string name,
        SqlServerVectorStoreRecordCollectionOptions<TRecord>? options = null)
    {
        Verify.NotNull(connection);
        Verify.NotNull(name);

        VectorStoreRecordPropertyReader propertyReader = new(typeof(TRecord),
            options?.RecordDefinition,
            new()
            {
                RequiresAtLeastOneVector = false,
                SupportsMultipleKeys = false,
                SupportsMultipleVectors = true,
            });

        if (VectorStoreRecordPropertyVerification.IsGenericDataModel(typeof(TRecord)))
        {
            VectorStoreRecordPropertyVerification.VerifyGenericDataModelKeyType(typeof(TRecord), options?.Mapper is not null, SqlServerConstants.SupportedKeyTypes);
        }
        else
        {
            propertyReader.VerifyKeyProperties(SqlServerConstants.SupportedKeyTypes);
        }
        propertyReader.VerifyDataProperties(SqlServerConstants.SupportedDataTypes, supportEnumerable: false);
        propertyReader.VerifyVectorProperties(SqlServerConstants.SupportedVectorTypes);

        this._sqlConnection = connection;
        this.CollectionName = name;
        // We need to create a copy, so any changes made to the option bag after
        // the ctor call do not affect this instance.
        this._options = options is null ? s_defaultOptions
            : new()
            {
                Schema = options.Schema,
                Mapper = options.Mapper,
                RecordDefinition = options.RecordDefinition,
            };
        this._propertyReader = propertyReader;

        if (options is not null && options.Mapper is not null)
        {
            this._mapper = options.Mapper;
        }
        else if (typeof(TRecord).IsGenericType && typeof(TRecord).GetGenericTypeDefinition() == typeof(VectorStoreGenericDataModel<>))
        {
            this._mapper = (new GenericRecordMapper<TKey>(propertyReader) as IVectorStoreRecordMapper<TRecord, IDictionary<string, object?>>)!;
        }
        else
        {
            propertyReader.VerifyHasParameterlessConstructor();

            this._mapper = new RecordMapper<TRecord>(propertyReader);
        }
    }

    /// <inheritdoc/>
    public string CollectionName { get; }

    /// <inheritdoc/>
    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        using SqlCommand command = SqlServerCommandBuilder.SelectTableName(
            this._sqlConnection, this._options.Schema, this.CollectionName);

        return await ExceptionWrapper.WrapAsync(this._sqlConnection, command,
            static async (cmd, ct) =>
            {
                using SqlDataReader reader = await cmd.ExecuteReaderAsync(ct).ConfigureAwait(false);
                return await reader.ReadAsync(ct).ConfigureAwait(false);
            }, cancellationToken, "CollectionExists", this.CollectionName).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
        => this.CreateCollectionAsync(ifNotExists: false, cancellationToken);

    /// <inheritdoc/>
    public Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
        => this.CreateCollectionAsync(ifNotExists: true, cancellationToken);

    private async Task CreateCollectionAsync(bool ifNotExists, CancellationToken cancellationToken)
    {
        foreach (var vectorProperty in this._propertyReader.VectorProperties)
        {
            if (vectorProperty.Dimensions is not > 0)
            {
                throw new InvalidOperationException($"Property {nameof(vectorProperty.Dimensions)} on {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.DataModelPropertyName}' must be set to a positive integer to create a collection.");
            }
        }

        using SqlCommand command = SqlServerCommandBuilder.CreateTable(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            ifNotExists,
            this._propertyReader.KeyProperty,
            this._propertyReader.DataProperties,
            this._propertyReader.VectorProperties);

        await ExceptionWrapper.WrapAsync(this._sqlConnection, command,
            static (cmd, ct) => cmd.ExecuteNonQueryAsync(ct),
            cancellationToken, "CreateCollection", this.CollectionName).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        using SqlCommand command = SqlServerCommandBuilder.DropTableIfExists(
            this._sqlConnection, this._options.Schema, this.CollectionName);

        await ExceptionWrapper.WrapAsync(this._sqlConnection, command,
            static (cmd, ct) => cmd.ExecuteNonQueryAsync(ct),
            cancellationToken, "DeleteCollection", this.CollectionName).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        using SqlCommand command = SqlServerCommandBuilder.DeleteSingle(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            key);

        await ExceptionWrapper.WrapAsync(this._sqlConnection, command,
            static (cmd, ct) => cmd.ExecuteNonQueryAsync(ct),
            cancellationToken, "Delete", this.CollectionName).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task DeleteBatchAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        using SqlCommand? command = SqlServerCommandBuilder.DeleteMany(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            keys);

        if (command is null)
        {
            return; // keys is empty, there is nothing to delete
        }

        await ExceptionWrapper.WrapAsync(this._sqlConnection, command,
            static (cmd, ct) => cmd.ExecuteNonQueryAsync(ct),
            cancellationToken, "DeleteBatch", this.CollectionName).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        bool includeVectors = options?.IncludeVectors is true;

        using SqlCommand command = SqlServerCommandBuilder.SelectSingle(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            key,
            includeVectors);

        using SqlDataReader reader = await ExceptionWrapper.WrapAsync(this._sqlConnection, command,
            static async (cmd, ct) =>
            {
                SqlDataReader reader = await cmd.ExecuteReaderAsync(ct).ConfigureAwait(false);
                await reader.ReadAsync(ct).ConfigureAwait(false);
                return reader;
            }, cancellationToken, "Get", this.CollectionName).ConfigureAwait(false);

        return reader.HasRows
            ? this._mapper.MapFromStorageToDataModel(
                new SqlDataReaderDictionary(reader, this._propertyReader.VectorPropertyStoragePropertyNames),
                new() { IncludeVectors = includeVectors })
            : default;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        bool includeVectors = options?.IncludeVectors is true;

        using SqlCommand? command = SqlServerCommandBuilder.SelectMany(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            keys,
            includeVectors);

        if (command is null)
        {
            yield break; // keys is empty
        }

        using SqlDataReader reader = await ExceptionWrapper.WrapAsync(this._sqlConnection, command,
            static (cmd, ct) => cmd.ExecuteReaderAsync(ct),
            cancellationToken, "GetBatch", this.CollectionName).ConfigureAwait(false);

        while (await ExceptionWrapper.WrapReadAsync(reader, cancellationToken, "GetBatch", this.CollectionName).ConfigureAwait(false))
        {
            yield return this._mapper.MapFromStorageToDataModel(
                new SqlDataReaderDictionary(reader, this._propertyReader.VectorPropertyStoragePropertyNames),
                new() { IncludeVectors = includeVectors });
        }
    }

    /// <inheritdoc/>
    public async Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        using SqlCommand command = SqlServerCommandBuilder.MergeIntoSingle(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            this._mapper.MapFromDataToStorageModel(record));

        return await ExceptionWrapper.WrapAsync(this._sqlConnection, command,
            async static (cmd, ct) =>
            {
                using SqlDataReader reader = await cmd.ExecuteReaderAsync(ct).ConfigureAwait(false);
                await reader.ReadAsync(ct).ConfigureAwait(false);
                return reader.GetFieldValue<TKey>(0);
            }, cancellationToken, "Upsert", this.CollectionName).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<TKey> UpsertBatchAsync(IEnumerable<TRecord> records,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        using SqlCommand? command = SqlServerCommandBuilder.MergeIntoMany(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            records.Select(record => this._mapper.MapFromDataToStorageModel(record)));

        if (command is null)
        {
            yield break; // records is empty
        }

        using SqlDataReader reader = await ExceptionWrapper.WrapAsync(this._sqlConnection, command,
            static (cmd, ct) => cmd.ExecuteReaderAsync(ct),
            cancellationToken, "GetBatch", this.CollectionName).ConfigureAwait(false);

        while (await ExceptionWrapper.WrapReadAsync(reader, cancellationToken, "GetBatch", this.CollectionName).ConfigureAwait(false))
        {
            yield return reader.GetFieldValue<TKey>(0);
        }
    }

    /// <inheritdoc/>
    public async Task<VectorSearchResults<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(vector);

        if (vector is not ReadOnlyMemory<float> allowed)
        {
            throw new NotSupportedException(
                $"The provided vector type {vector.GetType().FullName} is not supported by the SQL Server connector. " +
                $"Supported types are: {string.Join(", ", SqlServerConstants.SupportedVectorTypes.Select(l => l.FullName))}");
        }
#pragma warning disable CS0618 // Type or member is obsolete
        else if (options is not null && options.OldFilter is not null)
#pragma warning restore CS0618 // Type or member is obsolete
        {
            throw new NotSupportedException("The obsolete Filter is not supported by the SQL Server connector, use NewFilter instead.");
        }

        var searchOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._propertyReader.GetVectorPropertyOrSingle(searchOptions);

        using SqlCommand command = SqlServerCommandBuilder.SelectVector(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            vectorProperty,
            this._propertyReader.Properties,
            this._propertyReader.StoragePropertyNamesMap,
            searchOptions,
            allowed);

        return await ExceptionWrapper.WrapAsync(this._sqlConnection, command,
            (cmd, ct) =>
            {
                var results = this.ReadVectorSearchResultsAsync(cmd, searchOptions.IncludeVectors, ct);
                return Task.FromResult(new VectorSearchResults<TRecord>(results));
            }, cancellationToken, "VectorizedSearch", this.CollectionName).ConfigureAwait(false);
    }

    private async IAsyncEnumerable<VectorSearchResult<TRecord>> ReadVectorSearchResultsAsync(
        SqlCommand command,
        bool includeVectors,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        StorageToDataModelMapperOptions options = new() { IncludeVectors = includeVectors };
        var vectorPropertyStoragePropertyNames = includeVectors ? this._propertyReader.VectorPropertyStoragePropertyNames : [];
        using SqlDataReader reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

        int scoreIndex = -1;
        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            if (scoreIndex < 0)
            {
                scoreIndex = reader.GetOrdinal("score");
            }

            yield return new VectorSearchResult<TRecord>(
                this._mapper.MapFromStorageToDataModel(new SqlDataReaderDictionary(reader, vectorPropertyStoragePropertyNames), options),
                reader.GetDouble(scoreIndex));
        }
    }
}
