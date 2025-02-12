// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

/// <summary>
/// An implementation of <see cref="IVectorStore"/> backed by a SQL Server or Azure SQL database.
/// </summary>
public sealed class SqlServerVectorStore : IVectorStore, IDisposable
{
    internal const string DefaultSchema = "dbo";
    internal const int DefaultEmbeddingDimensionsCount = 1536;

    private readonly SqlConnection _connection;
    private readonly SqlServerClient _sqlServerClient;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqlServerVectorStore"/> class.
    /// </summary>
    /// <param name="connection">Database connection.</param>
    /// <param name="schema">Database schema of collection tables.</param>
    /// <param name="embeddingDimensionsCount">Number of dimensions that stored embeddings will use</param>
    public SqlServerVectorStore(SqlConnection connection, string schema = DefaultSchema, int embeddingDimensionsCount = DefaultEmbeddingDimensionsCount)
    {
        // TODO adsitnik: design:
        // 1. Do we need a ctor that takes the connection string and creates a connection?
        //    What is the story with pooling for the SqlConnection type?
        //    Does it maintain a private instance pool? Or a static one?
        // 2. Should we introduce an option bag for the schema and embeddingDimensionsCount?
        //    This would allow us to add more options in the future without breaking the API.
        this._connection = connection;
        this._sqlServerClient = new SqlServerClient(connection, schema, embeddingDimensionsCount);
    }

    /// <inheritdoc/>
    public void Dispose() => this._connection.Dispose();

    /// <inheritdoc/>
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null) where TKey : notnull
    {
        Verify.NotNull(name);

        throw new System.NotImplementedException();
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default)
        => this._sqlServerClient.GetTablesAsync(cancellationToken);
}
