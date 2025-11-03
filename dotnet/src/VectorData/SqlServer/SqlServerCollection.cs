// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data.Common;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using Microsoft.Data.SqlTypes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// An implementation of <see cref="VectorStoreCollection{TKey, TRecord}"/> backed by a SQL Server or Azure SQL database.
/// </summary>
#pragma warning disable CA1711 // Identifiers should not have incorrect suffix (Collection)
public class SqlServerCollection<TKey, TRecord>
#pragma warning restore CA1711
    : VectorStoreCollection<TKey, TRecord>
    where TKey : notnull
    where TRecord : class
{
    /// <summary>Metadata about vector store record collection.</summary>
    private readonly VectorStoreCollectionMetadata _collectionMetadata;

    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    private readonly string _connectionString;
    private readonly CollectionModel _model;
    private readonly SqlServerMapper<TRecord> _mapper;

    /// <summary>The database schema.</summary>
    private readonly string? _schema;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="connectionString">Database connection string.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="options">Optional configuration options.</param>
    [RequiresUnreferencedCode("The SQL Server provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The SQL Server provider is currently incompatible with NativeAOT.")]
    public SqlServerCollection(
        string connectionString,
        string name,
        SqlServerCollectionOptions? options = null)
        : this(
            connectionString,
            name,
            static options => typeof(TRecord) == typeof(Dictionary<string, object?>)
                ? throw new NotSupportedException(VectorDataStrings.NonDynamicCollectionWithDictionaryNotSupported(typeof(SqlServerDynamicCollection)))
                : new SqlServerModelBuilder().Build(typeof(TRecord), options.Definition, options.EmbeddingGenerator),
            options)
    {
    }

    internal SqlServerCollection(string connectionString, string name, Func<SqlServerCollectionOptions, CollectionModel> modelFactory, SqlServerCollectionOptions? options)
    {
        Verify.NotNullOrWhiteSpace(connectionString);
        Verify.NotNull(name);

        options ??= SqlServerCollectionOptions.Default;
        this._schema = options.Schema;

        this._connectionString = connectionString;
        this.Name = name;
        this._model = modelFactory(options);

        this._mapper = new SqlServerMapper<TRecord>(this._model);

        var connectionStringBuilder = new SqlConnectionStringBuilder(connectionString);

        this._collectionMetadata = new()
        {
            VectorStoreSystemName = SqlServerConstants.VectorStoreSystemName,
            VectorStoreName = connectionStringBuilder.InitialCatalog,
            CollectionName = name
        };
    }

    /// <inheritdoc/>
    public override string Name { get; }

    /// <inheritdoc/>
    public override async Task<bool> CollectionExistsAsync(CancellationToken cancellationToken = default)
    {
        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.SelectTableName(
            connection, this._schema, this.Name);

        return await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            "CollectionExists",
            async () =>
            {
                using SqlDataReader reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
                return await reader.ReadAsync(cancellationToken).ConfigureAwait(false);
            },
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override Task EnsureCollectionExistsAsync(CancellationToken cancellationToken = default)
        => this.CreateCollectionAsync(ifNotExists: true, cancellationToken);

    private async Task CreateCollectionAsync(bool ifNotExists, CancellationToken cancellationToken)
    {
        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.CreateTable(
            connection,
            this._schema,
            this.Name,
            ifNotExists,
            this._model);

        await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            "CreateCollection",
            () => command.ExecuteNonQueryAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override async Task EnsureCollectionDeletedAsync(CancellationToken cancellationToken = default)
    {
        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.DropTableIfExists(
            connection, this._schema, this.Name);

        await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            "DeleteCollection",
            () => command.ExecuteNonQueryAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override async Task DeleteAsync(TKey key, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.DeleteSingle(
            connection,
            this._schema,
            this.Name,
            this._model.KeyProperty,
            key);

        await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            "Delete",
            () => command.ExecuteNonQueryAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override async Task DeleteAsync(IEnumerable<TKey> keys, CancellationToken cancellationToken = default)
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
                        this._schema,
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
        catch (DbException ex)
        {
#if NET
            await transaction.RollbackAsync(cancellationToken).ConfigureAwait(false);
#else
            transaction.Rollback();
#endif

            throw new VectorStoreException(ex.Message, ex)
            {
                VectorStoreSystemName = SqlServerConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = "DeleteBatch"
            };
        }
        catch (Exception)
        {
#if NET
            await transaction.RollbackAsync(cancellationToken).ConfigureAwait(false);
#else
            transaction.Rollback();
#endif

            throw;
        }
    }

    /// <inheritdoc/>
    public override async Task<TRecord?> GetAsync(TKey key, RecordRetrievalOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        bool includeVectors = options?.IncludeVectors is true;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }

        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.SelectSingle(
            connection,
            this._schema,
            this.Name,
            this._model,
            key,
            includeVectors);

        return await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            operationName: "Get",
            async () =>
            {
                using SqlDataReader reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
                await reader.ReadAsync(cancellationToken).ConfigureAwait(false);
                return reader.HasRows
                    ? this._mapper.MapFromStorageToDataModel(reader, includeVectors)
                    : null;
            },
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<TRecord> GetAsync(IEnumerable<TKey> keys, RecordRetrievalOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        bool includeVectors = options?.IncludeVectors is true;
        if (includeVectors && this._model.EmbeddingGenerationRequired)
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
                this._schema,
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

            using SqlDataReader reader = await connection.ExecuteWithErrorHandlingAsync(
                this._collectionMetadata,
                operationName: "GetBatch",
                () => command.ExecuteReaderAsync(cancellationToken),
                cancellationToken).ConfigureAwait(false);

            while (true)
            {
                TRecord? record = await VectorStoreErrorHandler.RunOperationAsync<TRecord?, SqlException>(
                    this._collectionMetadata,
                    "GetBatch",
                    async () => await reader.ReadAsync(cancellationToken).ConfigureAwait(false)
                        ? this._mapper.MapFromStorageToDataModel(reader, includeVectors)
                        : null)
                        .ConfigureAwait(false);

                if (record is null)
                {
                    break;
                }

                yield return record;
            }
        } while (command.Parameters.Count == SqlServerConstants.MaxParameterCount);
    }

    /// <inheritdoc/>
    public override async Task UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        Dictionary<VectorPropertyModel, IReadOnlyList<Embedding>>? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (SqlServerModelBuilder.IsVectorPropertyTypeValidCore(vectorProperty.Type, out _))
            {
                continue;
            }

            // We have a vector property whose type isn't natively supported - we need to generate embeddings.
            Debug.Assert(vectorProperty.EmbeddingGenerator is not null);

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbedding<TRecord, Embedding<float>>(record, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new Dictionary<VectorPropertyModel, IReadOnlyList<Embedding>>(vectorPropertyCount);
                generatedEmbeddings[vectorProperty] = [await floatTask.ConfigureAwait(false)];
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
            this._schema,
            this.Name,
            this._model,
            record,
            generatedEmbeddings);

        await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            "Upsert",
            async () =>
            {
                using SqlDataReader reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);
                await reader.ReadAsync(cancellationToken).ConfigureAwait(false);
                // TODO: Currently unused (#11835), but will be injected into the record in the future.
                return reader.GetFieldValue<TKey>(0);
            },
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public override async Task UpsertAsync(IEnumerable<TRecord> records, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(records);

        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        Dictionary<VectorPropertyModel, IReadOnlyList<Embedding>>? generatedEmbeddings = null;

        var vectorPropertyCount = this._model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = this._model.VectorProperties[i];

            if (SqlServerModelBuilder.IsVectorPropertyTypeValidCore(vectorProperty.Type, out _))
            {
                continue;
            }

            // We have a vector property whose type isn't natively supported - we need to generate embeddings.
            Debug.Assert(vectorProperty.EmbeddingGenerator is not null);

            // We have a property with embedding generation; materialize the records' enumerable if needed, to
            // prevent multiple enumeration.
            if (recordsList is null)
            {
                recordsList = records is IReadOnlyList<TRecord> r ? r : records.ToList();

                if (recordsList.Count == 0)
                {
                    return;
                }

                records = recordsList;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>>(records, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new Dictionary<VectorPropertyModel, IReadOnlyList<Embedding>>(vectorPropertyCount);
                generatedEmbeddings[vectorProperty] = (IReadOnlyList<Embedding<float>>)await floatTask.ConfigureAwait(false);
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
                        this._schema,
                        this.Name,
                        this._model,
                        records.Skip(taken).Take(SqlServerConstants.MaxParameterCount / parametersPerRecord),
                        firstRecordIndex: taken,
                        generatedEmbeddings))
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
        catch (DbException ex)
        {
#if NET
            await transaction.RollbackAsync(cancellationToken).ConfigureAwait(false);
#else
            transaction.Rollback();
#endif

            throw new VectorStoreException(ex.Message, ex)
            {
                VectorStoreSystemName = SqlServerConstants.VectorStoreSystemName,
                VectorStoreName = this._collectionMetadata.VectorStoreName,
                CollectionName = this.Name,
                OperationName = "UpsertBatch"
            };
        }
        catch (Exception)
        {
#if NET
            await transaction.RollbackAsync(cancellationToken).ConfigureAwait(false);
#else
            transaction.Rollback();
#endif
            throw;
        }
    }

    #region Search

    /// <inheritdoc />
    public override async IAsyncEnumerable<VectorSearchResult<TRecord>> SearchAsync<TInput>(
        TInput searchValue,
        int top,
        VectorSearchOptions<TRecord>? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(searchValue);
        Verify.NotLessThan(top, 1);

        options ??= s_defaultVectorSearchOptions;
        if (options.IncludeVectors && this._model.EmbeddingGenerationRequired)
        {
            throw new NotSupportedException(VectorDataStrings.IncludeVectorsNotSupportedWithEmbeddingGeneration);
        }
#pragma warning disable CS0618 // Type or member is obsolete
        if (options.OldFilter is not null)
        {
            throw new NotSupportedException("The obsolete Filter is not supported by the SQL Server connector, use NewFilter instead.");
        }
#pragma warning restore CS0618 // Type or member is obsolete

        var vectorProperty = this._model.GetVectorPropertyOrSingle(options);

        SqlVector<float> vector = searchValue switch
        {
            SqlVector<float> v => v,
            ReadOnlyMemory<float> r => new(r),
            float[] f => new(f),
            Embedding<float> e => new(e.Vector),

            _ when vectorProperty.EmbeddingGenerator is IEmbeddingGenerator<TInput, Embedding<float>> generator
                => new(await generator.GenerateVectorAsync(searchValue, cancellationToken: cancellationToken).ConfigureAwait(false)),

            _ => vectorProperty.EmbeddingGenerator is null
                ? throw new NotSupportedException(VectorDataStrings.InvalidSearchInputAndNoEmbeddingGeneratorWasConfigured(searchValue.GetType(), SqlServerModelBuilder.SupportedVectorTypes))
                : throw new InvalidOperationException(VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(typeof(TInput), vectorProperty.EmbeddingGenerator.GetType()))
        };

#pragma warning disable CA2000 // Dispose objects before losing scope
        // Connection and command are going to be disposed by the ReadVectorSearchResultsAsync,
        // when the user is done with the results.
        SqlConnection connection = new(this._connectionString);
        SqlCommand command = SqlServerCommandBuilder.SelectVector(
            connection,
            this._schema,
            this.Name,
            vectorProperty,
            this._model,
            top,
            options,
            vector);
#pragma warning restore CA2000 // Dispose objects before losing scope

        await foreach (var record in this.ReadVectorSearchResultsAsync(connection, command, options.IncludeVectors, cancellationToken).ConfigureAwait(false))
        {
            yield return record;
        }
    }

    #endregion Search

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreCollectionMetadata) ? this._collectionMetadata :
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
            var vectorProperties = includeVectors ? this._model.VectorProperties : [];

            using SqlDataReader reader = await connection.ExecuteWithErrorHandlingAsync(
                this._collectionMetadata,
                operationName: "VectorizedSearch",
                () => command.ExecuteReaderAsync(cancellationToken),
                cancellationToken).ConfigureAwait(false);

            int scoreIndex = -1;
            while (await reader.ReadWithErrorHandlingAsync(
                this._collectionMetadata,
                operationName: "VectorizedSearch",
                cancellationToken).ConfigureAwait(false))
            {
                if (scoreIndex < 0)
                {
                    scoreIndex = reader.GetOrdinal("score");
                }

                yield return new VectorSearchResult<TRecord>(
                    this._mapper.MapFromStorageToDataModel(reader, includeVectors),
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
    public override async IAsyncEnumerable<TRecord> GetAsync(Expression<Func<TRecord, bool>> filter, int top,
        FilteredRecordRetrievalOptions<TRecord>? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
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
            this._schema,
            this.Name,
            this._model);

        using SqlDataReader reader = await connection.ExecuteWithErrorHandlingAsync(
            this._collectionMetadata,
            operationName: "GetAsync",
            () => command.ExecuteReaderAsync(cancellationToken),
            cancellationToken).ConfigureAwait(false);

        var vectorProperties = options.IncludeVectors ? this._model.VectorProperties : [];
        while (await reader.ReadWithErrorHandlingAsync(
                this._collectionMetadata,
                operationName: "GetAsync",
                cancellationToken).ConfigureAwait(false))
        {
            yield return this._mapper.MapFromStorageToDataModel(reader, options.IncludeVectors);
        }
    }
}
