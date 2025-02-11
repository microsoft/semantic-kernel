// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.Sqlite;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using VectorDataSpecificationTests.Support;

namespace SqliteIntegrationTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields (_connection) but is not disposable

internal sealed class SqliteTestStore : TestStore
{
    public static SqliteTestStore Instance { get; } = new();

    private SqliteConnection? _connection;
    public SqliteConnection Connection
        => this._connection ?? throw new InvalidOperationException("Call InitializeAsync() first");

    private SqliteVectorStore? _defaultVectorStore;
    public override IVectorStore DefaultVectorStore
        => this._defaultVectorStore ?? throw new InvalidOperationException("Call InitializeAsync() first");

    private SqliteTestStore()
    {
    }

    protected override async Task StartAsync()
    {
        this._connection = new SqliteConnection("Data Source=:memory:");

        await this.Connection.OpenAsync();

        if (!SqliteTestEnvironment.TryLoadSqliteVec(this.Connection))
        {
            this.Connection.Dispose();

            // Note that we ignore sqlite_vec loading failures; the tests are decorated with [SqliteVecRequired], which causes
            // them to be skipped if sqlite_vec isn't installed (better than an exception triggering failure here)
        }

        this._defaultVectorStore = new SqliteVectorStore(this.Connection);
    }

#if NET8_0_OR_GREATER
    protected override async Task StopAsync()
        => await this.Connection.DisposeAsync();
#else
    protected override Task StopAsync()
    {
        this.Connection.Dispose();
        return Task.CompletedTask;
    }
#endif
}
