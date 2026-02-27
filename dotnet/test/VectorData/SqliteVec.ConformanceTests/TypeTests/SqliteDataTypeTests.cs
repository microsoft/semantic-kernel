// Copyright (c) Microsoft. All rights reserved.

using SqliteVec.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Xunit;

namespace SqliteVec.ConformanceTests.TypeTests;

public class SqliteDataTypeTests(SqliteDataTypeTests.Fixture fixture)
    : DataTypeTests<int, DataTypeTests<int>.DefaultRecord>(fixture), IClassFixture<SqliteDataTypeTests.Fixture>
{
    public new class Fixture : DataTypeTests<int, DataTypeTests<int>.DefaultRecord>.Fixture
    {
        public override TestStore TestStore => SqliteTestStore.Instance;

        public override Type[] UnsupportedDefaultTypes { get; } =
        [
            typeof(byte),
            typeof(decimal),
            typeof(string[]),
        ];
    }
}
