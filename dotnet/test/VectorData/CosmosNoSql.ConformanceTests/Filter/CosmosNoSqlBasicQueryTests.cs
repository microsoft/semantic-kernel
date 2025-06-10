// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using VectorData.ConformanceTests.Filter;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosNoSql.ConformanceTests.Filter;

public class CosmosNoSqlBasicQueryTests(CosmosNoSqlBasicQueryTests.Fixture fixture)
    : BasicQueryTests<string>(fixture), IClassFixture<CosmosNoSqlBasicQueryTests.Fixture>
{
    public new class Fixture : BasicQueryTests<string>.QueryFixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
