// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using VectorDataSpecificationTests.Support;

namespace SqlServerIntegrationTests.Support;

public sealed class SqlServerTestStore : TestStore
{
    public static readonly SqlServerTestStore Instance = new();

    public override IVectorStore DefaultVectorStore
        => this._connectedStore ?? throw new InvalidOperationException("Not initialized");

    public override string DefaultDistanceFunction => DistanceFunction.CosineDistance;

    private SqlServerVectorStore? _connectedStore;

    protected override Task StartAsync()
    {
        if (string.IsNullOrWhiteSpace(SqlServerTestEnvironment.ConnectionString))
        {
            throw new InvalidOperationException("Connection string is not configured, set the SqlServer:ConnectionString environment variable");
        }

        this._connectedStore = new(SqlServerTestEnvironment.ConnectionString);

        return Task.CompletedTask;
    }
}
