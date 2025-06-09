// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using VectorData.ConformanceTests.Models;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace SqlServer.ConformanceTests.CRUD;

public class SqlServerBatchConformanceTests(SqlServerSimpleModelFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<SqlServerSimpleModelFixture>
{
    private const int SqlServerMaxParameters = 2_100;

    [ConditionalFact]
    public Task CanSplitBatchToAccountForMaxParameterLimit_WithVectors()
        => this.CanSplitBatchToAccountForMaxParameterLimit(includeVectors: true);

    [ConditionalFact]
    public Task CanSplitBatchToAccountForMaxParameterLimit_WithoutVectors()
        => this.CanSplitBatchToAccountForMaxParameterLimit(includeVectors: false);

    private async Task CanSplitBatchToAccountForMaxParameterLimit(bool includeVectors)
    {
        var collection = fixture.Collection;
        SimpleRecord<string>[] inserted = Enumerable.Range(0, SqlServerMaxParameters + 1).Select(i => new SimpleRecord<string>()
        {
            Id = fixture.GenerateNextKey<string>(),
            Number = 100 + i,
            Text = i.ToString(),
            Floats = Enumerable.Range(0, SimpleRecord<string>.DimensionCount).Select(j => (float)(i + j)).ToArray()
        }).ToArray();
        var keys = inserted.Select(record => record.Id).ToArray();

        Assert.Empty(await collection.GetAsync(keys).ToArrayAsync());
        await collection.UpsertAsync(inserted);

        var received = await collection.GetAsync(keys, new() { IncludeVectors = includeVectors }).ToArrayAsync();
        foreach (var record in inserted)
        {
            record.AssertEqual(this.GetRecord(received, record.Id), includeVectors, fixture.TestStore.VectorsComparable);
        }

        await collection.DeleteAsync(keys);
        Assert.Empty(await collection.GetAsync(keys).ToArrayAsync());
    }

    [ConditionalFact]
    public async Task UpsertBatchIsAtomic()
    {
        var collection = fixture.Collection;
        SimpleRecord<string>[] inserted = Enumerable.Range(0, SqlServerMaxParameters + 1).Select(i => new SimpleRecord<string>()
        {
            // The last Id is set to NULL, so it must not be inserted and the whole batch should fail
            Id = i < SqlServerMaxParameters ? fixture.GenerateNextKey<string>() : null!,
            Number = 100 + i,
            Text = i.ToString(),
            Floats = Enumerable.Range(0, SimpleRecord<string>.DimensionCount).Select(j => (float)(i + j)).ToArray()
        }).ToArray();

        var keys = inserted.Select(record => record.Id).Where(key => key is not null).ToArray();
        Assert.Empty(await collection.GetAsync(keys).ToArrayAsync());

        VectorStoreException ex = await Assert.ThrowsAsync<VectorStoreException>(() => collection.UpsertAsync(inserted));
        Assert.Equal("UpsertBatch", ex.OperationName);

        var metadata = collection.GetService(typeof(VectorStoreCollectionMetadata)) as VectorStoreCollectionMetadata;

        Assert.NotNull(metadata?.CollectionName);
        Assert.Equal(metadata.CollectionName, ex.CollectionName);

        // Make sure that no records were inserted!
        Assert.Empty(await collection.GetAsync(keys).ToArrayAsync());
    }
}
