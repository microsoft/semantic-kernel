// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSql.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace CosmosNoSql.ConformanceTests.TypeTests;

public class CosmosNoSqlDataTypeTests(CosmosNoSqlDataTypeTests.Fixture fixture)
    : DataTypeTests<string, DataTypeTests<string>.DefaultRecord>(fixture), IClassFixture<CosmosNoSqlDataTypeTests.Fixture>
{
    // Cosmos doesn't support DateTimeOffset with non-zero offset, so we convert it to UTC.
    // See https://github.com/dotnet/efcore/issues/35310
    [ConditionalFact(Skip = "Need to convert DateTimeOffset to UTC before sending to Cosmos")]
    public override Task DateTimeOffset()
        => this.Test<DateTimeOffset>(
            "DateTimeOffset",
            new DateTimeOffset(2020, 1, 1, 12, 30, 45, TimeSpan.FromHours(2)),
            new DateTimeOffset(2021, 2, 3, 13, 40, 55, TimeSpan.FromHours(3)),
            instantiationExpression: () => new DateTimeOffset(2020, 1, 1, 10, 30, 45, TimeSpan.FromHours(0)));

    public new class Fixture : DataTypeTests<string, DataTypeTests<string>.DefaultRecord>.Fixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;

        public override Type[] UnsupportedDefaultTypes { get; } =
        [
            typeof(byte),
            typeof(short),
            typeof(decimal),
            typeof(Guid),
            typeof(DateTime),
#if NET8_0_OR_GREATER
            typeof(DateOnly),
            typeof(TimeOnly)
#endif
        ];
    }
}
