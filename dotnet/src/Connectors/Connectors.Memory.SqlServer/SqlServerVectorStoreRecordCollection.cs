// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// An implementation of <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> backed by a SQL Server or Azure SQL database.
/// </summary>
public sealed class SqlServerVectorStoreRecordCollection<TKey, TRecord> : IVectorStoreRecordCollection<TKey, TRecord>
    where TKey : notnull
{
    private static readonly VectorSearchOptions<TRecord> s_defaultVectorSearchOptions = new();

    private readonly SqlConnection _sqlConnection;
    private readonly SqlServerVectorStoreOptions _options;
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerVectorStoreRecordCollection{TKey, TRecord}"/> class.
    /// </summary>
    /// <param name="connection">Database connection.</param>
    /// <param name="name">The name of the collection.</param>
    /// <param name="vectorStoreRecordDefinition">Optional record definition.</param>
    /// <param name="vectorStoreOptions">Optional configuration options.</param>
    public SqlServerVectorStoreRecordCollection(
        SqlConnection connection,
        string name,
        VectorStoreRecordDefinition? vectorStoreRecordDefinition = null,
        SqlServerVectorStoreOptions? vectorStoreOptions = null)
    {
        Verify.NotNull(connection);
        Verify.NotNull(name);

        VectorStoreRecordPropertyReader propertyReader = new(typeof(TRecord),
            vectorStoreRecordDefinition,
            new()
            {
                RequiresAtLeastOneVector = false,
                SupportsMultipleKeys = false,
                SupportsMultipleVectors = true,
            });

        propertyReader.VerifyHasParameterlessConstructor();
        propertyReader.VerifyKeyProperties(SqlServerConstants.SupportedKeyTypes);
        propertyReader.VerifyDataProperties(SqlServerConstants.SupportedDataTypes, supportEnumerable: false);
        propertyReader.VerifyVectorProperties(SqlServerConstants.SupportedVectorTypes);

        if (propertyReader.KeyProperty.AutoGenerate
            && !(typeof(TKey) == typeof(int) || typeof(TKey) == typeof(long) || typeof(TKey) == typeof(Guid)))
        {
            // SQL Server does not support auto-generated keys for types other than int, long, and Guid.
            throw new ArgumentException("Key property cannot be auto-generated.");
        }

        this._sqlConnection = connection;
        this.CollectionName = name;
        // We need to create a copy, so any changes made to the option bag after
        // the ctor call do not affect this instance.
        this._options = vectorStoreOptions is not null
            ? new() { Schema = vectorStoreOptions.Schema }
            : SqlServerVectorStoreOptions.Defaults;
        this._propertyReader = propertyReader;
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
            this._options,
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

        using SqlCommand command = SqlServerCommandBuilder.DeleteMany(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            keys);

        await ExceptionWrapper.WrapAsync(this._sqlConnection, command,
            static (cmd, ct) => cmd.ExecuteNonQueryAsync(ct),
            cancellationToken, "DeleteBatch", this.CollectionName).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public async Task<TRecord?> GetAsync(TKey key, GetRecordOptions? options = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(key);

        using SqlCommand command = SqlServerCommandBuilder.SelectSingle(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            key);

        using SqlDataReader reader = await ExceptionWrapper.WrapAsync(this._sqlConnection, command,
            static async (cmd, ct) =>
            {
                SqlDataReader reader = await cmd.ExecuteReaderAsync(ct).ConfigureAwait(false);
                await reader.ReadAsync(ct).ConfigureAwait(false);
                return reader;
            }, cancellationToken, "Get", this.CollectionName).ConfigureAwait(false);

        return reader.HasRows ? Map(reader, this._propertyReader) : default;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<TRecord> GetBatchAsync(IEnumerable<TKey> keys, GetRecordOptions? options = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(keys);

        using SqlCommand command = SqlServerCommandBuilder.SelectMany(
            this._sqlConnection,
            this._options.Schema,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            keys);

        using SqlDataReader reader = await ExceptionWrapper.WrapAsync(this._sqlConnection, command,
            static (cmd, ct) => cmd.ExecuteReaderAsync(ct),
            cancellationToken, "GetBatch", this.CollectionName).ConfigureAwait(false);

        while (await ExceptionWrapper.WrapReadAsync(reader, cancellationToken, "GetBatch", this.CollectionName).ConfigureAwait(false))
        {
            yield return Map(reader, this._propertyReader);
        }
    }

    /// <inheritdoc/>
    public async Task<TKey> UpsertAsync(TRecord record, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(record);

        using SqlCommand command = SqlServerCommandBuilder.MergeIntoSingle(
            this._sqlConnection,
            this._options,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            Map(record, this._propertyReader));

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

        using SqlCommand command = SqlServerCommandBuilder.MergeIntoMany(
            this._sqlConnection,
            this._options,
            this.CollectionName,
            this._propertyReader.KeyProperty,
            this._propertyReader.Properties,
            records.Select(record => Map(record, this._propertyReader)));

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
        else if (options is not null && options.Filter is not null)
#pragma warning restore CS0618 // Type or member is obsolete
        {
            throw new NotSupportedException("The obsolete Filter is not supported by the SQL Server connector, use NewFilter instead.");
        }

        var searchOptions = options ?? s_defaultVectorSearchOptions;
        var vectorProperty = this._propertyReader.GetVectorPropertyForSearch(searchOptions.VectorPropertyName);

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
                var results = this.ReadVectorSearchResultsAsync(cmd, ct);
                return Task.FromResult(new VectorSearchResults<TRecord>(results));
            }, cancellationToken, "VectorizedSearch", this.CollectionName).ConfigureAwait(false);
    }

    private async IAsyncEnumerable<VectorSearchResult<TRecord>> ReadVectorSearchResultsAsync(
        SqlCommand command,
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        using SqlDataReader reader = await command.ExecuteReaderAsync(cancellationToken).ConfigureAwait(false);

        int scoreIndex = -1;
        while (await reader.ReadAsync(cancellationToken).ConfigureAwait(false))
        {
            if (scoreIndex < 0)
            {
                scoreIndex = reader.GetOrdinal("score");
            }

            yield return new VectorSearchResult<TRecord>(
                Map(reader, this._propertyReader),
                reader.GetDouble(scoreIndex));
        }
    }

    private static Dictionary<string, object?> Map(TRecord record, VectorStoreRecordPropertyReader propertyReader)
    {
        Dictionary<string, object?> map = new(StringComparer.Ordinal);
        map[propertyReader.KeyProperty.DataModelPropertyName] = propertyReader.KeyPropertyInfo.GetValue(record);

        var dataProperties = propertyReader.DataProperties;
        for (int i = 0; i < dataProperties.Count; i++)
        {
            object value = propertyReader.DataPropertiesInfo[i].GetValue(record);
            map[dataProperties[i].DataModelPropertyName] = value;
        }
        var vectorProperties = propertyReader.VectorProperties;
        for (int i = 0; i < vectorProperties.Count; i++)
        {
            // We restrict the vector properties to ReadOnlyMemory<float> so the cast here is safe.
            ReadOnlyMemory<float> floats = (ReadOnlyMemory<float>)propertyReader.VectorPropertiesInfo[i].GetValue(record);
            // We know that SqlServer supports JSON serialization, so we can serialize the vector as JSON now,
            // so the SqlServerCommandBuilder does not need to worry about that.
            map[vectorProperties[i].DataModelPropertyName] = JsonSerializer.Serialize(floats);
        }

        return map;
    }

    private static TRecord Map(SqlDataReader reader, VectorStoreRecordPropertyReader propertyReader)
    {
        TRecord record = Activator.CreateInstance<TRecord>()!;
        SetValue(reader, record, propertyReader.KeyPropertyInfo, propertyReader.KeyProperty);
        var data = propertyReader.DataProperties;
        var dataInfo = propertyReader.DataPropertiesInfo;
        for (int i = 0; i < data.Count; i++)
        {
            SetValue(reader, record, dataInfo[i], data[i]);
        }

        var vector = propertyReader.VectorProperties;
        var vectorInfo = propertyReader.VectorPropertiesInfo;
        for (int i = 0; i < vector.Count; i++)
        {
            object value = reader[SqlServerCommandBuilder.GetColumnName(vector[i])];
            if (value is not DBNull)
            {
                ReadOnlyMemory<float>? embedding = null;

                try
                {
                    // This may fail if the user has stored a non-float array in the database
                    // (or serialized it in a different way).
                    embedding = JsonSerializer.Deserialize<ReadOnlyMemory<float>>((string)value);
                }
                catch (Exception ex)
                {
                    throw new VectorStoreRecordMappingException($"Failed to deserialize vector property '{vector[i].DataModelPropertyName}', it contained value '{value}'.", ex);
                }

                vectorInfo[i].SetValue(record, embedding);
            }
        }
        return record;

        static void SetValue(SqlDataReader reader, object record, PropertyInfo propertyInfo, VectorStoreRecordProperty property)
        {
            // If we got here, there should be no column name mismatch (the query would fail).
            object value = reader[SqlServerCommandBuilder.GetColumnName(property)];

            if (value is DBNull)
            {
                // There is no need to call the reflection to set the null,
                // as it's the default value of every .NET reference type field.
                return;
            }

            try
            {
                propertyInfo.SetValue(record, value);
            }
            catch (Exception ex)
            {
                throw new VectorStoreRecordMappingException($"Failed to set value '{value}' on property '{propertyInfo.Name}' of type '{propertyInfo.PropertyType.FullName}'.", ex);
            }
        }
    }
}
