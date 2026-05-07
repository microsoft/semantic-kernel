// Copyright (c) Microsoft. All rights reserved.

using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace SqlServer.ConformanceTests.TypeTests;

public class SqlServerKeyTypeTests(SqlServerKeyTypeTests.Fixture fixture)
    : KeyTypeTests(fixture), IClassFixture<SqlServerKeyTypeTests.Fixture>
{
    [ConditionalFact]
    public virtual Task Int() => this.Test<int>(8, supportsAutoGeneration: true);

    [ConditionalFact]
    public virtual Task Long() => this.Test<long>(8L, supportsAutoGeneration: true);

    [ConditionalFact]
    public virtual Task String() => this.Test<string>("foo", "bar");

    public new class Fixture : KeyTypeTests.Fixture
    {
        public override TestStore TestStore => SqlServerTestStore.Instance;
    }
}
