// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.Extensions.VectorData.Properties;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// An implementation of <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> backed by a SQL Server or Azure SQL database.
/// </summary>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix (Collection)
public sealed class SqlServerVectorStoreRecordCollection<TKey, TRecord>
#pragma warning restore CA1711
    : IVectorStoreRecordCollection<TKey, TRecord>
    where TKey : notnull
    where TRecord : notnull
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreRecordCollectionMetadata _collectionMetadata;

    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();
    private static readonly SqlServerVectorStoreRecordCollectionOptions<TRecord> s_defaultOptions = new();

    private readonly string _connectionString;
    private readonly SqlServerVectorStoreRecordCollectionOptions<TRecord> _options;
    private readonly VectorStoreRecordModel _model;
    private readonly RecordMapper<TRecord> _mapper;

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

        this._model = new VectorStoreRecordModelBuilder(SqlServerConstants.ModelBuildingOptions)
            .Build(typeof(TRecord), options?.RecordDefinition, options?.EmbeddingGenerator);

        this._connectionString = connectionString;
        this.Name = name;
        // We need to create a copy, so any changes made to the option bag after
        // the ctor call do not affect this instance.
        this._options = options is null
            ? s_defaultOptions
            : new()
            {
                Schema = options.Schema,
                RecordDefinition = options.RecordDefinition,
            };
        this._mapper = new RecordMapper<TRecord>(this._model);

        var connectionStringBuilder = new SqlConnectionStringBuilder(connectionString);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = SqlServerConstants.VectorStoreSystemName,
            VectorStoreName = connectionStringBuilder.InitialCatalog,
            CollectionName = name
        };
    }

    /// <inheritdoc/>
    public string Name { get; }

    /// <inheritdoc/>
    public async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.SelectTableName(
            connection, this._options.Schema, this.Name);

        return await ExceptionWrapper.WrapAsync(connection, command,
            static async (cmd, ct) =>
            {
                using SqlDataReader reader = await cmd.ExecuteReaderAsync(ct).ConfigureAwait(false);
                return await reader.ReadAsync(ct).ConfigureAwait(false);
            },
            "CollectionExists",
            this._collectionMetadata.VectorStoreName,
            this.Name,
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public Task CreateCollectionAsync(CancellationToken cancellationToken = default)
        => this.CreateCollectionAsync(ifNotExists: false, cancellationToken);

    /// <inheritdoc/>
    public Task CreateCollectionIfNotExistsAsync(CancellationToken cancellationToken = default)
        => this.CreateCollectionAsync(ifNotExists: true, cancellationToken);

    private async Task CreateCollectionAsync(bool ifNotExists, CancellationToken cancellationToken)
    {
        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.CreateTable(
            connection,
            this._options.Schema,
            this.Name,
            ifNotExists,
            this._model);

        await ExceptionWrapper.WrapAsync(connection, command,
            static (cmd, ct) => cmd.ExecuteNonQueryAsync(ct),
            "CreateCollection",
            this._collectionMetadata.VectorStoreName,
            this.Name,
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(CancellationToken cancellationToken = default)
    {
        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.DropTableIfExists(
            connection, this._options.Schema, this.Name);

        await ExceptionWrapper.WrapAsync(connection, command,
            static (cmd, ct) => cmd.ExecuteNonQueryAsync(ct),
            "DeleteCollection",
            this._collectionMetadata.VectorStoreName,
            this.Name,
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.DeleteSingle(
            connection,
            this._options.Schema,
            this.Name,
            this._model.KeyProperty,
            key);

        await ExceptionWrapper.WrapAsync(connection, command,
            static (cmd, ct) => cmd.ExecuteNonQueryAsync(ct),
            "Delete",
            this._collectionMetadata.VectorStoreName,
            this.Name,
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
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
                        this.Name,
                        this._model.KeyProperty,
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
                VectorStoreSystemName = SqlServerConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = "DeleteBatch"
            };
        }
    }

    /// <inheritdoc/>
    public async Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        bool includeVectors = options?.IncludeVectors is true;

        if (includeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.SelectSingle(
            connection,
            this._options.Schema,
            this.Name,
            this._model,
            key,
            includeVectors);

        using SqlDataReader reader = await ExceptionWrapper.WrapAsync(connection, command,
            static async (cmd, ct) =>
            {
                SqlDataReader reader = await cmd.ExecuteReaderAsync(ct).ConfigureAwait(false);
                await reader.ReadAsync(ct).ConfigureAwait(false);
                return reader;
            },
            "Get",
            this._collectionMetadata.VectorStoreName,
            this.Name,
            cancellationToken).ConfigureAwait(false);

        return reader.HasRows
            ? this._mapper.MapFromStorageToDataModel(
                new SqlDataReaderDictionary(reader, this._model.VectorProperties),
                new() { IncludeVectors = includeVectors })
            : default;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<TRecord> GetAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        bool includeVectors = options?.IncludeVectors is true;

        if (includeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

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
                this.Name,
                this._model,
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
                "GetBatch",
                this._collectionMetadata.VectorStoreName,
                this.Name,
                cancellationToken).ConfigureAwait(false);

            while (await ExceptionWrapper.WrapReadAsync(
                reader,
                "GetBatch",
                this._collectionMetadata.VectorStoreName,
                this.Name,
                cancellationToken).ConfigureAwait(false))
            {
                yield return this._mapper.MapFromStorageToDataModel(
                    new SqlDataReaderDictionary(reader, this._model.VectorProperties),
                    new() { IncludeVectors = includeVectors });
            }
        } while (command.Parameters.Count == SqlServerConstants.MaxParameterCount);
    }

    /// <inheritdoc/>
    public async Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        IReadOnlyList<Embedding>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (vectorProperty.EmbeddingGenerator is null)
            {
                continue;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbedding<TRecord, Embedding<float>, ReadOnlyMemory<float>>(record, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = [await floatTask.ConfigureAwait(false)];
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.MergeIntoSingle(
            connection,
            this._options.Schema,
            this.Name,
            this._model,
            this._mapper.MapFromDataToStorageModel(record, recordIndex: 0, generatedEmbeddings));

        return await ExceptionWrapper.WrapAsync(connection, command,
            async static (cmd, ct) =>
            {
                using SqlDataReader reader = await cmd.ExecuteReaderAsync(ct).ConfigureAwait(false);
                await reader.ReadAsync(ct).ConfigureAwait(false);
                return reader.GetFieldValue<TKey>(0);
            },
            "Upsert",
            this._collectionMetadata.VectorStoreName,
            this.Name,
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<IReadOnlyList<TKey>> UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        IReadOnlyList<Embedding>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (vectorProperty.EmbeddingGenerator is null)
            {
                continue;
            }

            // We have a property with embedding generation; materialize the records' enumerable if needed, to
            // prevent multiple enumeration.
            if (recordsList is null)
            {
                recordsList = records is IReadOnlyList<TRecord> r ? r : records.ToList();

                if (recordsList.Count == 0)
                {
                    return [];
                }

                records = recordsList;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>, ReadOnlyMemory<float>>(records, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = (IReadOnlyList<Embedding<float>>)await floatTask.ConfigureAwait(false);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        using SqlConnection connection = new(this._connectionString);
        await connection.OpenAsync(cancellationToken).ConfigureAwait(false);

        using SqlTransaction transaction = connection.BeginTransaction();
        int parametersPerRecord = this._model.Properties.Count;
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
                        this.Name,
                        this._model,
                        records.Skip(taken)
                               .Take(SqlServerConstants.MaxParameterCount / parametersPerRecord)
                               .Select((r, i) => this._mapper.MapFromDataToStorageModel(r, taken + i, generatedEmbeddings))))
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
                VectorStoreSystemName = SqlServerConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = "UpsertBatch"
            };
        }

        var keyProperty = this._model.KeyProperty;

        return records.Select(r => (TKey)keyProperty.GetValueAsObject(r)!).ToList();
    }

    #region Search

    /// <inheritdoc />
    public async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput value,
        int top,
        VectorSearchOptions<TRecord>? options = default,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
        where TInput : notnull
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        switch (vectorProperty.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, Embedding<float>> generator:
                var embedding = await generator.GenerateAsync(value, new() { Dimensions = vectorProperty.Dimensions }, cancellationToken).ConfigureAwait(false);

                await foreach (var record in this.SearchCoreAsync(embedding.Vector, top, vectorProperty, operationName: "Search", options, cancellationToken).ConfigureAwait(false))
                {
                    yield return record;
                }

                yield break;

            case null:
                throw new InvalidOperationException(VectorDataStrings.NoEmbeddingGeneratorWasConfiguredForSearch);

            default:
                throw new InvalidOperationException(
                    SqlServerConstants.SupportedVectorTypes.Contains(typeof(TInput))
                        ? string.Format(VectorDataStrings.EmbeddingTypePassedToSearchAsync)
                        : string.Format(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType, typeof(TInput).Name, vectorProperty.EmbeddingGenerator.GetType().Name));
        }
    }

    /// <inheritdoc />
    public IAsyncEnumerable<VectorSearchResult<TRecord>> SearchEmbeddingAsync<TVector>(
        TVector vector,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        options ??= s_defaultVectorSearchOptions;
        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        return this.SearchCoreAsync(vector, top, vectorProperty, operationName: "SearchEmbedding", options, cancellationToken);
    }

    private IAsyncEnumerable<VectorSearchResult<TRecord>> SearchCoreAsync<TVector>(
        TVector vector,
        int top,
        VectorStoreRecordVectorPropertyModel vectorProperty,
        string operationName,
        VectorSearchOptions<TRecord> options,
        CancellationToken cancellationToken = default)
        where TVector : notnull
    {
        Verify.NotNull(vector);
        Verify.NotLessThan(top, 1);

        if (vector is not ReadOnlyMemory<float> allowed)
        {
            throw new NotSupportedException(
                $"The provided vector type {vector.GetType().FullName} is not supported by the SQL Server connector. " +
                $"Supported types are: {string.Join(", ", SqlServerConstants.SupportedVectorTypes.Select(l => l.FullName))}");
        }
#pragma warning disable CS0618 // Type or member is obsolete
        else if (options.OldFilter is not null)
#pragma warning restore CS0618 // Type or member is obsolete
        {
            throw new NotSupportedException("The obsolete Filter is not supported by the SQL Server connector, use NewFilter instead.");
        }

        if (options.IncludeVectors && this._model.VectorProperties.Any(p => p.EmbeddingGenerator is not null))
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

#pragma warning disable CA2000 // Dispose objects before losing scope
        // Connection and command are going to be disposed by the ReadVectorSearchResultsAsync,
        // when the user is done with the results.
        SqlConnection connection = new(this._connectionString);
        SqlCommand command = SqlServerCommandBuilder.SelectVector(
            connection,
            this._options.Schema,
            this.Name,
            vectorProperty,
            this._model,
            top,
            options,
            allowed);
#pragma warning restore CA2000 // Dispose objects before losing scope

        return this.ReadVectorSearchResultsAsync(connection, command, options.IncludeVectors, cancellationToken);
    }

    /// <inheritdoc />
    [Obsolete("Use either SearchEmbeddingAsync to search directly on embeddings, or SearchAsync to handle embedding generation internally as part of the call.")]
    public IAsyncEnumerable<VectorSearchResult<TRecord>> VectorizedSearchAsync<TVector>(TVector vector, int top, VectorSearchOptions<TRecord>? options = null, CancellationToken cancellationToken = default)
        where TVector : notnull
        => this.SearchEmbeddingAsync(vector, top, options, cancellationToken);

    #endregion Search

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreRecordCollectionMetadata) ? this._collectionMetadata :
            serviceType.IsInstanceOfType(this) ? this :
            null;
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
            var vectorProperties = includeVectors ? this._model.VectorProperties : [];

            using SqlDataReader reader = await ExceptionWrapper.WrapAsync(connection, command,
                static (cmd, ct) => cmd.ExecuteReaderAsync(ct),
                "VectorizedSearch",
                this._collectionMetadata.VectorStoreName,
                this.Name,
                cancellationToken).ConfigureAwait(false);

            int scoreIndex = -1;
            while (await ExceptionWrapper.WrapReadAsync(
                reader,
                "VectorizedSearch",
                this._collectionMetadata.VectorStoreName,
                this.Name,
                cancellationToken).ConfigureAwait(false))
            {
                if (scoreIndex < 0)
                {
                    scoreIndex = reader.GetOrdinal("score");
                }

                yield return new VectorSearchResult<TRecord>(
                    this._mapper.MapFromStorageToDataModel(new SqlDataReaderDictionary(reader, vectorProperties), options),
                    reader.GetDouble(scoreIndex));
            }
        }
        finally
        {
            command.Dispose();
            connection.Dispose();
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        GetFilteredRecordOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(filter);
        Verify.NotLessThan(top, 1);

        options ??= new();

        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.SelectWhere(
            filter,
            top,
            options,
            connection,
            this._options.Schema,
            this.Name,
            this._model);

        using SqlDataReader reader = await ExceptionWrapper.WrapAsync(connection, command,
            static (cmd, ct) => cmd.ExecuteReaderAsync(ct),
            "GetAsync", this._collectionMetadata.VectorStoreName, this.Name, cancellationToken).ConfigureAwait(false);

        var vectorProperties = options.IncludeVectors ? this._model.VectorProperties : [];
        StorageToDataModelMapperOptions mapperOptions = new() { IncludeVectors = options.IncludeVectors };
        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return this._mapper.MapFromStorageToDataModel(new SqlDataReaderDictionary(reader, vectorProperties), mapperOptions);
        }
    }
}
