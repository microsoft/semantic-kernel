// Copyright (c) Microsoft. All rights reserved.

using InMemoryIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace InMemoryIntegrationTests.CRUD;

public class InMemoryBatchConformanceTests(InMemorySimpleModelFixture fixture)
    : BatchConformanceTests<int>(fixture), IClassFixture<InMemorySimpleModelFixture>
{
    // InMemory always returns the vectors (IncludeVectors = false isn't respected)
    public override async Task GetBatchAsync_WithoutVectors()
    {
        var expectedRecords = fixture.TestData.Take(2); // the last two records can get deleted by other tests
        var ids = expectedRecords.Select(record => record.Id);

        var received = await fixture.Collection.GetAsync(ids, new() { IncludeVectors = false }).ToArrayAsync();

        foreach (var record in expectedRecords)
        {
            record.AssertEqual(this.GetRecord(received, record.Id), includeVectors: true, fixture.TestStore.VectorsComparable);
        }
    }
}
