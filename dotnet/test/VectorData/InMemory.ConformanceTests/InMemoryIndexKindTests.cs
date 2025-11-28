// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace InMemory.ConformanceTests;

public class InMemoryIndexKindTests(InMemoryIndexKindTests.Fixture fixture)
    : IndexKindTests<int>(fixture), IClassFixture<InMemoryIndexKindTests.Fixture>
{
    public new class Fixture() : IndexKindTests<int>.Fixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;
    }
}
