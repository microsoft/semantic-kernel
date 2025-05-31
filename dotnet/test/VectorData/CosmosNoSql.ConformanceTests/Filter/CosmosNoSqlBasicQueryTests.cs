// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSqlIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace CosmosNoSqlIntegrationTests.Filter;

public class CosmosNoSqlBasicQueryTests(CosmosNoSqlBasicQueryTests.Fixture fixture)
    : BasicQueryTests<string>(fixture), IClassFixture<CosmosNoSqlBasicQueryTests.Fixture>
{
    public new class Fixture : BasicQueryTests<string>.QueryFixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
