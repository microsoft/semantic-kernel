// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace InMemory.ConformanceTests.ModelTests;

public class InMemoryBasicModelTests(InMemoryBasicModelTests.Fixture fixture)
    : BasicModelTests<int>(fixture), IClassFixture<InMemoryBasicModelTests.Fixture>
{
    public override async Task GetAsync_single_record(bool includeVectors)
    {
        if (includeVectors)
        {
            await base.GetAsync_single_record(includeVectors);
            return;
        }

        // InMemory always returns the vectors (IncludeVectors = false isn't respected)
        var expectedRecord = fixture.TestData[0];
        var received = await fixture.Collection.GetAsync(expectedRecord.Key, new() { IncludeVectors = false });

        expectedRecord.AssertEqual(received, includeVectors: true, fixture.TestStore.VectorsComparable);
    }

    public override async Task GetAsync_multiple_records(bool includeVectors)
    {
        if (includeVectors)
        {
            await base.GetAsync_multiple_records(includeVectors);
            return;
        }

        // InMemory always returns the vectors (IncludeVectors = false isn't respected)
        var expectedRecords = fixture.TestData.Take(2); // the last two records can get deleted by other tests
        var ids = expectedRecords.Select(record => record.Key);

        var received = await fixture.Collection.GetAsync(ids, new() { IncludeVectors = false }).ToArrayAsync();

        foreach (var record in expectedRecords)
        {
            record.AssertEqual(
                received.Single(r => r.Key.Equals(record.Key)),
                includeVectors: true,
                fixture.TestStore.VectorsComparable);
        }
    }

    public override async Task GetAsync_with_filter(bool includeVectors)
    {
        if (includeVectors)
        {
            await base.GetAsync_with_filter(includeVectors);
            return;
        }

        // InMemory always returns the vectors (IncludeVectors = false isn't respected)
        var expectedRecord = fixture.TestData[0];

        var results = await this.Collection.GetAsync(
            r => r.Number == 1,
            top: 2,
            new() { IncludeVectors = includeVectors })
            .ToListAsync();

        var receivedRecord = Assert.Single(results);
        expectedRecord.AssertEqual(receivedRecord, includeVectors: true, fixture.TestStore.VectorsComparable);
    }

    public new class Fixture : BasicModelTests<int>.Fixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;
    }
}
