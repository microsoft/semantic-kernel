// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace InMemory.ConformanceTests.CRUD;

public class InMemoryNoDataConformanceTests(InMemoryNoDataConformanceTests.Fixture fixture)
    : NoDataConformanceTests<string>(fixture), IClassFixture<InMemoryNoDataConformanceTests.Fixture>
{
    public new class Fixture : NoDataConformanceTests<string>.Fixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;
    }
}
