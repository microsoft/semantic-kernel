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

    private readonly string _connectionString;
    private readonly SqlServerVectorStoreRecordCollectionOptions<TRecord> _options;
    private readonly VectorStoreRecordPropertyReader _propertyReader;
    private readonly IVectorStoreRecordMapper<TRecord, IDictionary<string, object?>> _mapper;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="connectionString">Database connection string.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options.</param>
    public SqlServerVectorStoreRecordCollection(
        string connectionString,
        string name,
        SqlServerVectorStoreRecordCollectionOptions<TRecord>? options = null)
    {
        Verify.NotNullOrWhiteSpace(connectionString);
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

        this._connectionString = connectionString;
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
        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.SelectTableName(
            connection, this._options.Schema, this.CollectionName);

        return await ExceptionWrapper.WrapAsync(connection, command,
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

        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.CreateTable(
            connection,
            this._options.Schema,
            this.CollectionName,
            ifNotExists,
            this._propertyReader.KeyProperty,
            this._propertyReader.DataProperties,
            this._propertyReader.VectorProperties);

        await ExceptionWrapper.WrapAsync(connection, command,
            static (cmd, ct) => cmd.ExecuteNonQueryAsync(ct),
            cancellationToken, "CreateCollection", this.CollectionName).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.DropTableIfExists(
            connection, this._options.Schema, this.CollectionName);

        await ExceptionWrapper.WrapAsync(connection, command,
            static (cmd, ct) => cmd.ExecuteNonQueryAsync(ct),
            cancellationToken, "DeleteCollection", this.CollectionName).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.DeleteSingle(
            connection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            key);

        await ExceptionWrapper.WrapAsync(connection, command,
            static (cmd, ct) => cmd.ExecuteNonQueryAsync(ct),
            cancellationToken, "Delete", this.CollectionName).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task DeleteBatchAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        using SqlConnection connection = new(this._connectionString);
        await connection.OpenAsync(cancellationToken).ConfigureAwait(false);

        using SqlTransaction transaction = connection.BeginTransaction();
        int taken = 0;

        try
        {
            while (true)
            {
#if NET
                SqlCommand command = new("", connection, transaction);
                await using (command.ConfigureAwait(false))
#else
                using (SqlCommand command = new("", connection, transaction))
#endif
                {
                    if (!SqlServerCommandBuilder.DeleteMany(
                        command,
                        this._options.Schema,
                        this.CollectionName,
                        this._propertyReader.KeyProperty,
                        keys.Skip(taken).Take(SqlServerConstants.MaxParameterCount)))
                    {
                        break; // keys is empty, there is nothing to delete
                    }

                    checked
                    {
                        taken += command.Parameters.Count;
                    }

                    await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
                }
            }

            if (taken > 0)
            {
#if NET
                await transaction.CommitAsync(cancellationToken).ConfigureAwait(false);
#else
                transaction.Commit();
#endif
            }
        }
        catch (Exception ex)
        {
#if NET
            await transaction.RollbackAsync(cancellationToken).ConfigureAwait(false);
#else
            transaction.Rollback();
#endif

            throw new VectorStoreOperationException(ex.Message, ex)
            {
                OperationName = "DeleteBatch",
                VectorStoreType = ExceptionWrapper.VectorStoreType,
                CollectionName = this.CollectionName
            };
        }
    }

    /// <inheritdoc/>
    public async Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        bool includeVectors = options?.IncludeVectors is true;

        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.SelectSingle(
            connection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            key,
            includeVectors);

        using SqlDataReader reader = await ExceptionWrapper.WrapAsync(connection, command,
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

        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = connection.CreateCommand();
        int taken = 0;

        do
        {
            if (command.Parameters.Count > 0)
            {
                command.Parameters.Clear(); // We reuse the same command for the next batch.
            }

            if (!SqlServerCommandBuilder.SelectMany(
                command,
                this._options.Schema,
                this.CollectionName,
                this._propertyReader.KeyProperty,
                this._propertyReader.Properties,
                keys.Skip(taken).Take(SqlServerConstants.MaxParameterCount),
                includeVectors))
            {
                yield break; // keys is empty
            }

            checked
            {
                taken += command.Parameters.Count;
            }

            using SqlDataReader reader = await ExceptionWrapper.WrapAsync(connection, command,
                static (cmd, ct) => cmd.ExecuteReaderAsync(ct),
                cancellationToken, "GetBatch", this.CollectionName).ConfigureAwait(false);

            while (await ExceptionWrapper.WrapReadAsync(reader, cancellationToken, "GetBatch", this.CollectionName).ConfigureAwait(false))
            {
                yield return this._mapper.MapFromStorageToDataModel(
                    new SqlDataReaderDictionary(reader, this._propertyReader.VectorPropertyStoragePropertyNames),
                    new() { IncludeVectors = includeVectors });
            }
        } while (command.Parameters.Count == SqlServerConstants.MaxParameterCount);
    }

    /// <inheritdoc/>
    public async Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.MergeIntoSingle(
            connection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            this._mapper.MapFromDataToStorageModel(record));

        return await ExceptionWrapper.WrapAsync(connection, command,
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

        using SqlConnection connection = new(this._connectionString);
        await connection.OpenAsync(cancellationToken).ConfigureAwait(false);

        using SqlTransaction transaction = connection.BeginTransaction();
        int parametersPerRecord = this._propertyReader.Properties.Count;
        int taken = 0;

        try
        {
            while (true)
            {
#if NET
                SqlCommand command = new("", connection, transaction);
                await using (command.ConfigureAwait(false))
#else
                using (SqlCommand command = new("", connection, transaction))
#endif
                {
                    if (!SqlServerCommandBuilder.MergeIntoMany(
                        command,
                        this._options.Schema,
                        this.CollectionName,
                        this._propertyReader.KeyProperty,
                        this._propertyReader.Properties,
                        records.Skip(taken)
                               .Take(SqlServerConstants.MaxParameterCount / parametersPerRecord)
                               .Select(this._mapper.MapFromDataToStorageModel)))
                    {
                        break; // records is empty
                    }

                    checked
                    {
                        taken += (command.Parameters.Count / parametersPerRecord);
                    }

                    await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
                }
            }

            if (taken > 0)
            {
#if NET
                await transaction.CommitAsync(cancellationToken).ConfigureAwait(false);
#else
                transaction.Commit();
#endif
            }
        }
        catch (Exception ex)
        {
#if NET
            await transaction.RollbackAsync(cancellationToken).ConfigureAwait(false);
#else
            transaction.Rollback();
#endif

            throw new VectorStoreOperationException(ex.Message, ex)
            {
                OperationName = "UpsertBatch",
                VectorStoreType = ExceptionWrapper.VectorStoreType,
                CollectionName = this.CollectionName
            };
        }

        if (typeof(TRecord) == typeof(VectorStoreGenericDataModel<TKey>))
        {
            foreach (var record in records)
            {
                yield return ((VectorStoreGenericDataModel<TKey>)(object)record!).Key;
            }
        }
        else
        {
            var keyProperty = this._propertyReader.KeyPropertyInfo;
            foreach (var record in records)
            {
                yield return (TKey)keyProperty.GetValue(record)!;
            }
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

#pragma warning disable CA2000 // Dispose objects before losing scope
        // This connection will be disposed by the ReadVectorSearchResultsAsync
        // when the user is done with the results.
        SqlConnection connection = new(this._connectionString);
#pragma warning restore CA2000 // Dispose objects before losing scope
        using SqlCommand command = SqlServerCommandBuilder.SelectVector(
            connection,
            this._options.Schema,
            this.CollectionName,
            vectorProperty,
            this._propertyReader.Properties,
            this._propertyReader.StoragePropertyNamesMap,
            searchOptions,
            allowed);

        return await ExceptionWrapper.WrapAsync(connection, command,
            (cmd, ct) =>
            {
                var results = this.ReadVectorSearchResultsAsync(connection, cmd, searchOptions.IncludeVectors, ct);
                return Task.FromResult(new VectorSearchResults<TRecord>(results));
            }, cancellationToken, "VectorizedSearch", this.CollectionName).ConfigureAwait(false);
    }

    private async IAsyncEnumerable<VectorSearchResult<TRecord>> ReadVectorSearchResultsAsync(
        SqlConnection connection,
        SqlCommand command,
        bool includeVectors,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        try
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
        finally
        {
            connection.Dispose();
        }
    }
}
