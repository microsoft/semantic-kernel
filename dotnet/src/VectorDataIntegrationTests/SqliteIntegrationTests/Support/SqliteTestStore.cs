﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using VectorDataSpecificationTests.Support;

namespace SqliteIntegrationTests.Support;

internal sealed class SqliteTestStore : TestStore
{
    private string? _databasePath;

    public static SqliteTestStore Instance { get; } = new();

    private SqliteVectorStore? _defaultVectorStore;
    public override IVectorStore DefaultVectorStore
        => this._defaultVectorStore ?? throw new InvalidOperationException("Call InitializeAsync() first");

    private SqliteTestStore()
    {
    }

    protected override Task StartAsync()
    {
        this._databasePath = Path.GetTempFileName();
        this._defaultVectorStore = new SqliteVectorStore($"Data Source={this._databasePath}");
        return Task.CompletedTask;
    }

    protected override Task StopAsync()
    {
        File.Delete(this._databasePath!);
        this._databasePath = null;
        return Task.CompletedTask;
    }
}
