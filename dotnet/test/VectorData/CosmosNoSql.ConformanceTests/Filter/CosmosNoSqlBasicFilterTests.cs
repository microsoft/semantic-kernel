// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using VectorData.ConformanceTests.Filter;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosNoSql.ConformanceTests.Filter;

public class CosmosNoSqlBasicFilterTests(CosmosNoSqlBasicFilterTests.Fixture fixture)
    : BasicFilterTests<string>(fixture), IClassFixture<CosmosNoSqlBasicFilterTests.Fixture>
{
    public new class Fixture : BasicFilterTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
