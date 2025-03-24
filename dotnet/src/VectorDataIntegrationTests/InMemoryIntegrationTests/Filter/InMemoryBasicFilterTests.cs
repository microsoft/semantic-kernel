// Copyright (c) Microsoft. All rights reserved.

using InMemoryIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace PostgresIntegrationTests.Filter;

public class InMemoryBasicFilterTests(InMemoryBasicFilterTests.Fixture fixture)
    : BasicFilterTests<int>(fixture), IClassFixture<InMemoryBasicFilterTests.Fixture>
{
    public new class Fixture : BasicFilterTests<int>.Fixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;
    }
}
