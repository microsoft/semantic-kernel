// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSQLIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace CosmosNoSQLIntegrationTests.Filter;

public class CosmosNoSQLBasicFilterTests(CosmosNoSQLBasicFilterTests.Fixture fixture)
    : BasicFilterTests<string>(fixture), IClassFixture<CosmosNoSQLBasicFilterTests.Fixture>
{
    public new class Fixture : BasicFilterTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosNoSQLTestStore.Instance;
    }
}
