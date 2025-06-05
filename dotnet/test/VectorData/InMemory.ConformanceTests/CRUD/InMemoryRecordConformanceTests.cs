// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace InMemory.ConformanceTests.CRUD;

public class InMemoryRecordConformanceTests(InMemorySimpleModelFixture fixture)
    : RecordConformanceTests<int>(fixture), IClassFixture<InMemorySimpleModelFixture>
{
    // InMemory always returns the vectors (IncludeVectors = false isn't respected)
    public override async Task GetAsync_WithoutVectors()
    {
        var expectedRecord = fixture.TestData[0];
        var received = await fixture.Collection.GetAsync(expectedRecord.Id, new() { IncludeVectors = false });

        expectedRecord.AssertEqual(received, includeVectors: true, fixture.TestStore.VectorsComparable);
    }
}
