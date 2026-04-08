// Copyright (c) Microsoft. All rights reserved.

// TEMPORARY: This test class exists to work around a current SQL Server 2025 limitation where tables with
// vector indexes are read-only. Once this limitation is lifted, these tests should be removed and the
// standard conformance tests in SqlServerIndexKindTests should be enabled instead (by removing the Skip on DiskAnn).
//
// The workaround is to:
// 1. Create the table without the vector index (using IndexKind.Flat).
// 2. Insert data while the table is still writable.
// 3. Create the DiskANN vector index via raw SQL.
// 4. Create a new collection instance with IndexKind.DiskAnn to route searches through VECTOR_SEARCH().

using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;
using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace SqlServer.ConformanceTests;

public class SqlServerDiskAnnVectorSearchTests(
    SqlServerDiskAnnVectorSearchTests.Fixture fixture)
    : IClassFixture<SqlServerDiskAnnVectorSearchTests.Fixture>
{
    private const string CollectionName = "DiskAnnVectorSearchTests";

    /// <summary>
    /// Tests that approximate vector search via VECTOR_SEARCH() returns correct results
    /// when a DiskANN index exists on the table.
    /// </summary>
    [ConditionalFact]
    public async Task VectorSearch_WithDiskAnnIndex()
    {
        using var collection = this.CreateDiskAnnCollection();

        var result = await collection.SearchAsync(
            new ReadOnlyMemory<float>([10, 30, 50]), top: 1).SingleAsync();

        Assert.NotNull(result);
        Assert.Equal(2, result.Record.Int);
    }

    /// <summary>
    /// Tests that VECTOR_SEARCH() correctly returns multiple results ordered by distance.
    /// </summary>
    [ConditionalFact]
    public async Task VectorSearch_WithDiskAnnIndex_TopN()
    {
        using var collection = this.CreateDiskAnnCollection();

        var results = await collection.SearchAsync(
            new ReadOnlyMemory<float>([10, 30, 50]), top: 3).ToListAsync();

        Assert.Equal(3, results.Count);
        // The closest match should be the exact vector [10, 30, 50]
        Assert.Equal(2, results[0].Record.Int);
    }

    /// <summary>
    /// Tests that VECTOR_SEARCH() throws when a LINQ filter is specified,
    /// since SQL Server's VECTOR_SEARCH only supports post-filtering.
    /// </summary>
    [ConditionalFact]
    public async Task VectorSearch_WithDiskAnnIndex_WithFilter_Throws()
    {
        using var collection = this.CreateDiskAnnCollection();

        var exception = await Assert.ThrowsAsync<NotSupportedException>(
            async () => await collection.SearchAsync(
                new ReadOnlyMemory<float>([10, 30, 50]),
                top: 1,
                new VectorSearchOptions<SearchRecord>
                {
                    Filter = r => r.Int == 2
                }).SingleAsync());

        Assert.Contains("VECTOR_SEARCH", exception.Message);
    }

    private VectorStoreCollection<int, SearchRecord> CreateDiskAnnCollection()
    {
        VectorStoreCollectionDefinition definition = new()
        {
            Properties =
            [
                new VectorStoreKeyProperty(nameof(SearchRecord.Key), typeof(int)),
                new VectorStoreDataProperty(nameof(SearchRecord.Int), typeof(int)),
                new VectorStoreVectorProperty(nameof(SearchRecord.Vector), typeof(ReadOnlyMemory<float>), dimensions: 3)
                {
                    IndexKind = IndexKind.DiskAnn,
                    DistanceFunction = DistanceFunction.CosineDistance
                }
            ]
        };

        return fixture.TestStore.CreateCollection<int, SearchRecord>(CollectionName, definition);
    }

    public class SearchRecord
    {
        public int Key { get; set; }
        public int Int { get; set; }
        public ReadOnlyMemory<float> Vector { get; set; }
    }

    // TEMPORARY: This fixture works around the SQL Server 2025 read-only vector index limitation
    // by creating the table without a vector index, inserting data, and then creating the index.
    // See SqlServerIndexKindTests.DiskAnn for the standard (currently skipped) conformance test.
    public class Fixture : VectorStoreFixture, IAsyncLifetime
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;

        public override async Task InitializeAsync()
        {
            await base.InitializeAsync();

            var connectionString = SqlServerTestStore.Instance.ConnectionString;

            // Step 1: Create a "flat" collection (no vector index) and insert data.
            VectorStoreCollectionDefinition flatDefinition = new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty(nameof(SearchRecord.Key), typeof(int)),
                    new VectorStoreDataProperty(nameof(SearchRecord.Int), typeof(int)),
                    new VectorStoreVectorProperty(nameof(SearchRecord.Vector), typeof(ReadOnlyMemory<float>), dimensions: 3)
                    {
                        IndexKind = IndexKind.Flat,
                        DistanceFunction = DistanceFunction.CosineDistance
                    }
                ]
            };

            using var flatCollection = this.TestStore.CreateCollection<int, SearchRecord>(CollectionName, flatDefinition);
            await flatCollection.EnsureCollectionDeletedAsync();
            await flatCollection.EnsureCollectionExistsAsync();

            SearchRecord[] records =
            [
                new() { Key = 1, Int = 1, Vector = new([1, 2, 3]) },
                new() { Key = 2, Int = 2, Vector = new([10, 30, 50]) },
                new() { Key = 3, Int = 3, Vector = new([100, 40, 70]) }
            ];

            await flatCollection.UpsertAsync(records);
            await this.TestStore.WaitForDataAsync(flatCollection, records.Length);

            // Step 2: Create the DiskANN vector index now that data is already in the table.
            using var connection = new SqlConnection(connectionString);
            await connection.OpenAsync();

            using (var enablePreview = new SqlCommand(
                "ALTER DATABASE SCOPED CONFIGURATION SET PREVIEW_FEATURES = ON;", connection))
            {
                await enablePreview.ExecuteNonQueryAsync();
            }

            using (var createIndex = new SqlCommand(
                $"CREATE VECTOR INDEX index_{CollectionName}_Vector ON [{CollectionName}]([Vector]) WITH (METRIC = 'COSINE', TYPE = 'DISKANN');",
                connection))
            {
                await createIndex.ExecuteNonQueryAsync();
            }
        }

        public override async Task DisposeAsync()
        {
            // Clean up the table
            var connectionString = SqlServerTestStore.Instance.ConnectionString;
            using var connection = new SqlConnection(connectionString);
            await connection.OpenAsync();
            using var command = new SqlCommand($"DROP TABLE IF EXISTS [{CollectionName}]", connection);
            await command.ExecuteNonQueryAsync();

            await base.DisposeAsync();
        }
    }
}
