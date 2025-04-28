// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSQLIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace CosmosNoSQLIntegrationTests.Filter;

public class CosmosNoSQLBasicQueryTests(CosmosNoSQLBasicQueryTests.Fixture fixture)
    : BasicQueryTests<string>(fixture), IClassFixture<CosmosNoSQLBasicQueryTests.Fixture>
{
    public new class Fixture : BasicQueryTests<string>.QueryFixture
    {
        public override TestStore TestStore => CosmosNoSQLTestStore.Instance;
    }
}
