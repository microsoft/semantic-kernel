// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace InMemory.ConformanceTests;

public class InMemoryFilterTests(InMemoryFilterTests.Fixture fixture)
    : FilterTests<int>(fixture), IClassFixture<InMemoryFilterTests.Fixture>
{
    public new class Fixture : FilterTests<int>.Fixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;

        // BaseFilterTests attempts to create two InMemoryVectorStoreRecordCollection with different .NET types:
        // 1. One for strongly-typed mapping (TRecord=FilterRecord)
        // 2. One for dynamic mapping (TRecord=Dictionary<string, object?>)
        // Unfortunately, InMemoryVectorStore does not allow mapping the same collection name to different types;
        // at the same time, it simply evaluates all filtering via .NET AsQueryable(), so actual test coverage
        // isn't very important here. So we disable the dynamic tests.
        public override bool TestDynamic => false;
    }
}
