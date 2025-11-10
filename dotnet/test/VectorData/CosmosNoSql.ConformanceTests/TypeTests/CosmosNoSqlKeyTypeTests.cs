// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace CosmosNoSql.ConformanceTests.TypeTests;

public class CosmosNoSqlKeyTypeTests(CosmosNoSqlKeyTypeTests.Fixture fixture)
    : KeyTypeTests(fixture), IClassFixture<CosmosNoSqlKeyTypeTests.Fixture>
{
    [ConditionalFact]
    public virtual Task String() => this.Test<string>("foo", "bar");

    public new class Fixture : KeyTypeTests.Fixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
    }
}
