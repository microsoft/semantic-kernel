// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Xunit;

namespace PgVector.ConformanceTests.TypeTests;

public class PostgresDataTypeTests(PostgresDataTypeTests.Fixture fixture)
    : DataTypeTests<Guid, DataTypeTests<Guid>.DefaultRecord>(fixture), IClassFixture<PostgresDataTypeTests.Fixture>
{
    // Npgsql maps DateTime to timestamptz by default, and so requires UTC DateTimes (the base test uses Unspecified).
    public override Task DateTime()
        => Assert.ThrowsAsync<ArgumentException>(base.DateTime);

    public virtual Task DateTime_utc()
        => this.Test<DateTime>(
            "DateTime",
            System.DateTime.SpecifyKind(new DateTime(2020, 1, 1, 12, 30, 45), DateTimeKind.Utc),
            System.DateTime.SpecifyKind(new DateTime(2021, 2, 3, 13, 40, 55), DateTimeKind.Utc),
            instantiationExpression: () => System.DateTime.SpecifyKind(new DateTime(2020, 1, 1, 12, 30, 45), DateTimeKind.Utc));

    // PostgreSQL does not support representing an offset, so only DateTimeOffsets with offset=0 are supported.
    public override Task DateTimeOffset()
        => Assert.ThrowsAsync<ArgumentException>(base.DateTimeOffset);

    // PostgreSQL does not support representing an offset, so only DateTimeOffsets with offset=0 are supported.
    public virtual Task DateTimeOffset_with_offset_zero()
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
