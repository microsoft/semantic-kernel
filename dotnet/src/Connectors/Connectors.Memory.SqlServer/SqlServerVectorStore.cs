// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
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
            ? new() { Schema = options.Schema }
            : SqlServerVectorStoreOptions.Defaults;
    }

    /// <inheritdoc/>
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null) where TKey : notnull
    {
        Verify.NotNull(name);

        return new SqlServerVectorStoreRecordCollection<TKey, TRecord>(
            this._connectionString,
            name,
            new()
            {
                Schema = this._options.Schema,
                RecordDefinition = vectorStoreRecordDefinition
            });
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using SqlConnection connection = new(this._connectionString);
        using SqlCommand command = SqlServerCommandBuilder.SelectTableNames(connection, this._options.Schema);

        using SqlDataReader reader = await ExceptionWrapper.WrapAsync(connection, command,
            static (cmd, ct) => cmd.ExecuteReaderAsync(ct),
            cancellationToken, "ListCollection").ConfigureAwait(false);

        while (await ExceptionWrapper.WrapReadAsync(reader, cancellationToken, "ListCollection").ConfigureAwait(false))
        {
            yield return reader.GetString(reader.GetOrdinal("table_name"));
        }
    }
}
