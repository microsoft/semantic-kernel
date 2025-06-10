// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests.Filter;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace InMemory.ConformanceTests.Filter;

public class InMemoryBasicQueryTests(InMemoryBasicQueryTests.Fixture fixture)
    : BasicQueryTests<int>(fixture), IClassFixture<InMemoryBasicQueryTests.Fixture>
{
    public new class Fixture : BasicQueryTests<int>.QueryFixture
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
