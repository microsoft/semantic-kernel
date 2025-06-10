// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace InMemory.ConformanceTests.CRUD;

public class InMemoryDynamicRecordConformanceTests(InMemoryDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<int>(fixture), IClassFixture<InMemoryDynamicDataModelFixture>
{
    // InMemory always returns the vectors (IncludeVectors = false isn't respected)
    public override async Task GetAsync_WithoutVectors()
    {
        var expectedRecord = fixture.TestData[0];

        var received = await fixture.Collection.GetAsync(
            (int)expectedRecord[DynamicDataModelFixture<int>.KeyPropertyName]!,
            new() { IncludeVectors = false });

        AssertEquivalent(expectedRecord, received, includeVectors: true, fixture.TestStore.VectorsComparable);
    }
}
