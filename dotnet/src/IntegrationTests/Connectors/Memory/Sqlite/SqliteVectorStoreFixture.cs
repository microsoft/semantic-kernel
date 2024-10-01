// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Sqlite;

public class SqliteVectorStoreFixture : IAsyncLifetime
{
    public SqliteConnection Connection { get; }

    public SqliteVectorStoreFixture()
    {
        this.Connection = new SqliteConnection("Data Source=:memory:");
    }

    public async Task DisposeAsync()
    {
        await this.Connection.DisposeAsync();
    }

    public async Task InitializeAsync()
    {
        const string VectorSearchExtensionName = "vec0";

        await this.Connection.OpenAsync();

        this.Connection.LoadExtension(VectorSearchExtensionName);
    }
}
