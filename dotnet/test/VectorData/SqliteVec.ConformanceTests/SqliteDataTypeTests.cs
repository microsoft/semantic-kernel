// Copyright (c) Microsoft. All rights reserved.

using SqliteVec.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace SqliteVec.ConformanceTests;

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
            typeof(Guid),
            typeof(DateTime),
            typeof(DateTimeOffset),
            typeof(string[]),
#if NET8_0_OR_GREATER
            typeof(DateOnly),
            typeof(TimeOnly)
#endif
        ];
    }
}
