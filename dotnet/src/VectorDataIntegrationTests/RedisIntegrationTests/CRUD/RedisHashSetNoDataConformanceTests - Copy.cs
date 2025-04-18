// Copyright (c) Microsoft. All rights reserved.

using RedisIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace RedisIntegrationTests.CRUD;

public class RedisHashSetNoDataConformanceTests(RedisHashSetNoDataConformanceTests.Fixture fixture)
    : NoDataConformanceTests<string>(fixture), IClassFixture<RedisHashSetNoDataConformanceTests.Fixture>
{
    [ConditionalFact]
    public override async Task GetAsyncReturnsInsertedRecord_WithoutVectors()
    {
        var expectedRecord = fixture.TestData[0];

        // When using HashSets there is no way to distinguish between no fields being returned and
        // the record not existing.
        Assert.Null(await fixture.Collection.GetAsync(expectedRecord.Id, new() { IncludeVectors = false }));
    }

    [ConditionalFact]
    public override Task UpsertAsyncCanInsertNewRecord_WithoutVectors()
    {
        // When using HashSets there is no way to distinguish between no fields being returned and
        // the record not existing so this test isn't useful.
        return Task.CompletedTask;
    }

    [ConditionalFact]
    public override Task UpsertAsyncCanUpdateExistingRecord_WithoutVectors()
    {
        // When using HashSets there is no way to distinguish between no fields being returned and
        // the record not existing so this test isn't useful.
        return Task.CompletedTask;
    }

    public new class Fixture : NoDataConformanceTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.HashSetInstance;
    }
}
