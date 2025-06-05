// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSqlIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace CosmosNoSqlIntegrationTests.Filter;

public class CosmosNoSqlBasicFilterTests(CosmosNoSqlBasicFilterTests.Fixture fixture)
    : BasicFilterTests<string>(fixture), IClassFixture<CosmosNoSqlBasicFilterTests.Fixture>
{
    public new class Fixture : BasicFilterTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
