// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using VectorDataSpecificationTests.Support;

namespace SqlServerIntegrationTests.Support;

public sealed class SqlServerTestStore : TestStore, IDisposable
{
    public static readonly SqlServerTestStore Instance = new();

    public override IVectorStore DefaultVectorStore
        => this._connectedStore ?? throw new InvalidOperationException("Not initialized");

    public override string DefaultDistanceFunction => DistanceFunction.CosineDistance;

    private SqlServerVectorStore? _connectedStore;

    protected override async Task StartAsync()
    {
        if (string.IsNullOrWhiteSpace(SqlServerTestEnvironment.ConnectionString))
        {
            throw new InvalidOperationException("Connection string is not configured, set the SqlServer:ConnectionString environment variable");
        }

#pragma warning disable CA2000 // Dispose objects before losing scope
        SqlConnection connection = new(SqlServerTestEnvironment.ConnectionString);
#pragma warning restore CA2000 // Dispose objects before losing scope
        await connection.OpenAsync();

        this._connectedStore = new(connection);
    }

    public void Dispose() => this._connectedStore?.Dispose();
}
