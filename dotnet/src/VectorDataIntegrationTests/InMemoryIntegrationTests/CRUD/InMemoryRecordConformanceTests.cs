// Copyright (c) Microsoft. All rights reserved.

using InMemoryIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace InMemoryIntegrationTests.CRUD;

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
