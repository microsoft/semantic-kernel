// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using VectorDataSpecificationTests.Support;

namespace SqlServerIntegrationTests.Support;

public sealed class SqlServerTestStore : TestStore
{
    public static readonly SqlServerTestStore Instance = new();

    public override IVectorStore DefaultVectorStore
        => this._connectedStore ?? throw new InvalidOperationException("Not initialized");

    private SqlServerVectorStore? _connectedStore;

    protected override async Task StartAsync()
    {
        if (string.IsNullOrWhiteSpace(SqlServerTestEnvironment.ConnectionString))
        {
            throw new InvalidOperationException("Connection string is not configured, set the SqlServer:ConnectionString environment variable");
        }

        SqlConnection connection = new(SqlServerTestEnvironment.ConnectionString);
        await connection.OpenAsync();

        this._connectedStore = new(connection);
    }
}
