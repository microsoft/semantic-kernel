// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace InMemory.ConformanceTests.ModelTests;

public class InMemoryNoDataModelTests(InMemoryNoDataModelTests.Fixture fixture)
    : NoDataModelTests<string>(fixture), IClassFixture<InMemoryNoDataModelTests.Fixture>
{
    public new class Fixture : NoDataModelTests<string>.Fixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;
    }
}
