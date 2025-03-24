// Copyright (c) Microsoft. All rights reserved.

using InMemoryIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace PostgresIntegrationTests.Filter;

public class InMemoryBasicQueryTests(InMemoryBasicQueryTests.Fixture fixture)
    : BasicQueryTests<int>(fixture), IClassFixture<InMemoryBasicQueryTests.Fixture>
{
    public new class Fixture : BasicQueryTests<int>.QueryFixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;
    }
}
