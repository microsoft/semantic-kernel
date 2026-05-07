// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace SqlServer.ConformanceTests.ModelTests;

public class SqlServerBasicModelTests(SqlServerBasicModelTests.Fixture fixture)
    : BasicModelTests<string>(fixture), IClassFixture<SqlServerBasicModelTests.Fixture>
{
    private const int SqlServerMaxParameters = 2_100;

    [ConditionalFact]
    private async Task Split_batches_to_account_for_max_parameter_limit()
    {
        var collection = fixture.Collection;
        Record[] inserted = Enumerable.Range(0, SqlServerMaxParameters + 1).Select(i => new Record()
        {
            Key = fixture.GenerateNextKey<string>(),
            Number = 100 + i,
            Text = i.ToString(),
            Vector = Enumerable.Range(0, 3).Select(j => (float)(i + j)).ToArray()
        }).ToArray();
        var keys = inserted.Select(record => record.Key).ToArray();

        Assert.Empty(await collection.GetAsync(keys).ToArrayAsync());
        await collection.UpsertAsync(inserted);

        var received = await collection.GetAsync(keys).ToArrayAsync();
        foreach (var record in inserted)
        {
            record.AssertEqual(
                received.Single(r => r.Key.Equals(record.Key, StringComparison.Ordinal)),
                includeVectors: false,
                fixture.TestStore.VectorsComparable);
        }

        await collection.DeleteAsync(keys);
        Assert.Empty(await collection.GetAsync(keys).ToArrayAsync());
    }

    [ConditionalFact]
    public async Task Upsert_batch_is_atomic()
    {
        var collection = fixture.Collection;
        Record[] inserted = Enumerable.Range(0, SqlServerMaxParameters + 1).Select(i => new Record()
        {
            // The last Key is set to NULL, so it must not be inserted and the whole batch should fail
            Key = i < SqlServerMaxParameters ? fixture.GenerateNextKey<string>() : null!,
            Number = 100 + i,
            Text = i.ToString(),
            Vector = Enumerable.Range(0, 3).Select(j => (float)(i + j)).ToArray()
        }).ToArray();

        var keys = inserted.Select(record => record.Key).Where(key => key is not null).ToArray();
        Assert.Empty(await collection.GetAsync(keys).ToArrayAsync());

        VectorStoreException ex = await Assert.ThrowsAsync<VectorStoreException>(() => collection.UpsertAsync(inserted));
        Assert.Equal("UpsertBatch", ex.OperationName);

        var metadata = collection.GetService(typeof(VectorStoreCollectionMetadata)) as VectorStoreCollectionMetadata;

        Assert.NotNull(metadata?.CollectionName);
        Assert.Equal(metadata.CollectionName, ex.CollectionName);

        // Make sure that no records were inserted!
        Assert.Empty(await collection.GetAsync(keys).ToArrayAsync());
    }

    public new class Fixture : BasicModelTests<string>.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
