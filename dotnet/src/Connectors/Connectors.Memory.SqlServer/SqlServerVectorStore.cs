// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// An implementation of <see cref="IVectorStore"/> backed by a SQL Server or Azure SQL database.
/// </summary>
public sealed class SqlServerVectorStore : IVectorStore
{
    private readonly string _connectionString;
    private readonly SqlServerVectorStoreOptions _options;

    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreRecordDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreRecordKeyProperty("Key", typeof(string))] };

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerVectorStore"/> class.
    /// </summary>
    /// <param name="connectionString">The connection string.</param>
    /// <param name="options">Optional configuration options.</param>
    public SqlServerVectorStore(string connectionString, SqlServerVectorStoreOptions? options = null)
    {
        Verify.NotNullOrWhiteSpace(connectionString);

        this._connectionString = connectionString;
        // We need to create a copy, so any changes made to the option bag after
        // the ctor call do not affect this instance.
        this._options = options is not null
            ? new() { Schema = options.Schema, EmbeddingGenerator = options.EmbeddingGenerator }
            : SqlServerVectorStoreOptions.Defaults;

        var connectionStringBuilder = new SqlConnectionStringBuilder(connectionString);

        this._metadata = new()
        {
            VectorStoreSystemName = SqlServerConstants.VectorStoreSystemName,
            VectorStoreName = connectionStringBuilder.InitialCatalog
        };
    }

    /// <inheritdoc/>
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
        where TRecord : notnull
    {
        Verify.NotNull(name);

        return new SqlServerVectorStoreRecordCollection<TKey, TRecord>(
            this._connectionString,
            name,
            new()
            {
                Schema = this._options.Schema,
                RecordDefinition = vectorStoreRecordDefinition,
                EmbeddingGenerator = this._options.EmbeddingGenerator
            });
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.SelectTableNames(connection, this._options.Schema);

        using SqlDataReader reader = await ExceptionWrapper.WrapAsync(
            connection,
            command,
            static (cmd, ct) => cmd.ExecuteReaderAsync(ct),
            operationName: "ListCollectionNames",
            vectorStoreName: this._metadata.VectorStoreName,
            cancellationToken: cancellationToken).ConfigureAwait(false);

        while (await ExceptionWrapper.WrapReadAsync(
            reader,
            operationName: "ListCollectionNames",
            vectorStoreName: this._metadata.VectorStoreName,
            cancellationToken: cancellationToken).ConfigureAwait(false))
        {
            yield return reader.GetString(reader.GetOrdinal("table_name"));
        }
    }

    /// <inheritdoc />
    public Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.DeleteCollectionAsync(cancellationToken);
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreMetadata) ? this._metadata :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
