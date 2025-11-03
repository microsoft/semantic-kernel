// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace PgVector.ConformanceTests.TypeTests;

public class PostgresKeyTypeTests(PostgresKeyTypeTests.Fixture fixture)
    : KeyTypeTests(fixture), IClassFixture<PostgresKeyTypeTests.Fixture>
{
    [ConditionalFact]
    public virtual Task Int() => this.Test<int>(8);

    [ConditionalFact]
    public virtual Task Long() => this.Test<long>(8L);

    [ConditionalFact]
    public virtual Task String() => this.Test<string>("foo");

    public new class Fixture : KeyTypeTests.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;
    }
}
