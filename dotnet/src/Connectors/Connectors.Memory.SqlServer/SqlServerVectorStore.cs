// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// An implementation of <see cref="IVectorStore"/> backed by a SQL Server or Azure SQL database.
/// </summary>
public sealed class SqlServerVectorStore : IVectorStore, IDisposable
{
    private readonly SqlConnection _connection;
    private readonly SqlServerVectorStoreOptions _options;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerVectorStore"/> class.
    /// </summary>
    /// <param name="connection">Database connection.</param>
    /// <param name="options">Optional configuration options.</param>
    public SqlServerVectorStore(SqlConnection connection, SqlServerVectorStoreOptions? options = null)
    {
        this._connection = connection;
        // We need to create a copy, so any changes made to the option bag after
        // the ctor call do not affect this instance.
        this._options = options is not null
            ? new() { Schema = options.Schema }
            : SqlServerVectorStoreOptions.Defaults;
    }

    /// <inheritdoc/>
    public void Dispose() => this._connection.Dispose();

    /// <inheritdoc/>
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null) where TKey : notnull
    {
        Verify.NotNull(name);

        return new SqlServerVectorStoreRecordCollection<TKey, TRecord>(
            this._connection,
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
        using SqlCommand command = SqlServerCommandBuilder.SelectTableNames(this._connection, this._options.Schema);

        using SqlDataReader reader = await ExceptionWrapper.WrapAsync(this._connection, command,
            static (cmd, ct) => cmd.ExecuteReaderAsync(ct),
            cancellationToken, "ListCollection").ConfigureAwait(false);

        while (await ExceptionWrapper.WrapReadAsync(reader, cancellationToken, "ListCollection").ConfigureAwait(false))
        {
            yield return reader.GetString(reader.GetOrdinal("table_name"));
        }
    }
}
