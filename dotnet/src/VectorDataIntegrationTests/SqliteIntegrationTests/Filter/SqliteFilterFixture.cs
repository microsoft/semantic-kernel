// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.Sqlite;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using SqliteIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;

namespace SqliteIntegrationTests.Filter;

public class SqliteFilterFixture : FilterFixtureBase<ulong>
{
    public SqliteConnection Connection { get; private set; }
    public SqliteVectorStore DefaultVectorStore { get; private set; }

    public override async Task InitializeAsync()
    {
        this.Connection = new SqliteConnection("Data Source=:memory:");

        await this.Connection.OpenAsync();

        // Note that we ignore sqlite_vec loading failures; the tests are decorated with [SqliteVecRequired], which causes
        // them to be skipped if sqlite_vec isn't installed (better than an exception triggering failure here)
        if (!SqliteTestEnvironment.TryLoadSqliteVec(this.Connection))
        {
            this.Connection.Dispose();

            return;
        }

        this.DefaultVectorStore = new SqliteVectorStore(this.Connection);

        await base.InitializeAsync();
    }

    protected override IVectorStore GetVectorStore()
        => this.DefaultVectorStore;

    protected override string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;

    // Override to remove the string array property, which isn't (currently) supported on SQLite
    protected override VectorStoreRecordDefinition GetRecordDefinition()
        => new()
        {
            Properties = base.GetRecordDefinition().Properties.Where(p => p.PropertyType != typeof(string[])).ToList()
        };

    public override async Task DisposeAsync()
    {
        await base.DisposeAsync();
        this.Connection.Dispose();
    }
}
