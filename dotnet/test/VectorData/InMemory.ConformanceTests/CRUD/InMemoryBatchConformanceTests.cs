// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace InMemory.ConformanceTests.CRUD;

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
