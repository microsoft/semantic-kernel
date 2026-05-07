// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosNoSql.ConformanceTests;

public class CosmosNoSqlFilterTests(CosmosNoSqlFilterTests.Fixture fixture)
    : FilterTests<string>(fixture), IClassFixture<CosmosNoSqlFilterTests.Fixture>
{
    public new class Fixture : FilterTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
