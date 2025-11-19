// Copyright (c) Microsoft. All rights reserved.

using SqliteVec.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace SqliteVec.ConformanceTests.TypeTests;

public class SqliteKeyTypeTests(SqliteKeyTypeTests.Fixture fixture)
    : KeyTypeTests(fixture), IClassFixture<SqliteKeyTypeTests.Fixture>
{
    [ConditionalFact]
    public virtual Task Int() => this.Test<int>(8, 9);

    [ConditionalFact]
    public virtual Task Long() => this.Test<long>(8L, 9L);

    [ConditionalFact]
    public virtual Task String() => this.Test<string>("foo", "bar");

    public new class Fixture : KeyTypeTests.Fixture
    {
        public override TestStore TestStore => SqliteTestStore.Instance;
    }
}
