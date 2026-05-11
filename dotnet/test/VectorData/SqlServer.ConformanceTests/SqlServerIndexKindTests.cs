// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;
using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace SqlServer.ConformanceTests;

public class SqlServerIndexKindTests(SqlServerIndexKindTests.Fixture fixture)
    : IndexKindTests<int>(fixture), IClassFixture<SqlServerIndexKindTests.Fixture>
{
    // Latest version vector indexes are only available in Azure SQL, not in on-prem SQL Server.
    // They also require at least 100 rows before the vector index can be created,
    // so we override the test to insert data first, then create the index.
    [ConditionalFact]
    [AzureSqlRequired]
    public virtual async Task DiskAnn()
    {
        const string CollectionName = "IndexKindTests_DiskAnn";

        // Step 1: Create the table using Flat index (no vector index) so we can insert data.
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

        using var flatCollection = fixture.TestStore.CreateCollection<int, SearchRecord>(CollectionName, flatDefinition);
        await flatCollection.EnsureCollectionDeletedAsync();
        await flatCollection.EnsureCollectionExistsAsync();

        try
        {
            // Step 2: Insert the 3 test rows + 97 filler rows to meet the 100-row minimum.
            SearchRecord[] testRecords =
            [
                new() { Key = 1, Int = 1, Vector = new([1, 2, 3]) },
                new() { Key = 2, Int = 2, Vector = new([10, 30, 50]) },
                new() { Key = 3, Int = 3, Vector = new([100, 40, 70]) }
            ];

            await flatCollection.UpsertAsync(testRecords);

            var fillerRecords = Enumerable.Range(100, 97)
                .Select(i => new SearchRecord
                {
                    Key = i,
                    Int = i,
                    Vector = new([i * 0.1f, i * 0.2f, i * 0.3f])
                })
                .ToArray();

            await flatCollection.UpsertAsync(fillerRecords);

            // Step 3: Create the DiskANN vector index via raw SQL now that data is in the table.
            using var connection = new SqlConnection(SqlServerTestStore.Instance.ConnectionString);
            await connection.OpenAsync();

            using (var createIndex = new SqlCommand(
                $"CREATE VECTOR INDEX index_{CollectionName}_Vector ON [{CollectionName}]([Vector]) WITH (METRIC = 'COSINE', TYPE = 'DISKANN');",
                connection))
            {
                await createIndex.ExecuteNonQueryAsync();
            }

            // Step 4: Create a new collection instance with DiskAnn to route searches through VECTOR_SEARCH().
            VectorStoreCollectionDefinition diskAnnDefinition = new()
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

            using var diskAnnCollection = fixture.TestStore.CreateCollection<int, SearchRecord>(CollectionName, diskAnnDefinition);

            var result = await diskAnnCollection.SearchAsync(new ReadOnlyMemory<float>([10, 30, 50]), top: 1).SingleAsync();

            Assert.NotNull(result);
            Assert.Equal(2, result.Record.Int);
        }
        finally
        {
            await flatCollection.EnsureCollectionDeletedAsync();
        }
    }

    public new class Fixture() : IndexKindTests<int>.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
