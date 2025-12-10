// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Xunit;

namespace PgVector.ConformanceTests.TypeTests;

public class PostgresDataTypeTests(PostgresDataTypeTests.Fixture fixture)
    : DataTypeTests<Guid, DataTypeTests<Guid>.DefaultRecord>(fixture), IClassFixture<PostgresDataTypeTests.Fixture>
{
    // PostgreSQL does not support representing an offset, so only DateTimeOffsets with offset=0 are supported.
    public override Task DateTimeOffset()
        => this.Test<DateTimeOffset>(
            "DateTimeOffset",
            new DateTimeOffset(2020, 1, 1, 12, 30, 45, TimeSpan.FromHours(0)),
            new DateTimeOffset(2021, 2, 3, 13, 40, 55, TimeSpan.FromHours(0)),
            instantiationExpression: () => new DateTimeOffset(2020, 1, 1, 12, 30, 45, TimeSpan.FromHours(0)));

    public new class Fixture : DataTypeTests<Guid, DataTypeTests<Guid>.DefaultRecord>.Fixture
    {
        public override TestStore TestStore => PostgresTestStore.Instance;

        public override Type[] UnsupportedDefaultTypes { get; } =
        [
            typeof(byte),
#if NET
            typeof(DateOnly),
            typeof(TimeOnly),
#endif
        ];
    }
}
