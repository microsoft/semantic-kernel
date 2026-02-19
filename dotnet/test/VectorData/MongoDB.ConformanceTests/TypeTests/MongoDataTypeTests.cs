// Copyright (c) Microsoft. All rights reserved.

using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Xunit;

namespace MongoDB.ConformanceTests.TypeTests;

public class MongoDataTypeTests(MongoDataTypeTests.Fixture fixture)
    : DataTypeTests<string, DataTypeTests<string>.DefaultRecord>(fixture), IClassFixture<MongoDataTypeTests.Fixture>
{
    public override Task Decimal()
        => this.Test<decimal>(
            "Decimal", 8.5m, 9.5m,
            isFilterable: false); // Operand type is not supported for $vectorSearch: decimal

    public override Task DateTime()
        => this.Test<DateTime>(
            "DateTime",
            new DateTime(2020, 1, 1, 12, 30, 45, DateTimeKind.Utc),
            new DateTime(2021, 2, 3, 13, 40, 55, DateTimeKind.Utc),
            instantiationExpression: () => new DateTime(2020, 1, 1, 12, 30, 45),
            isFilterable: false); // Operand type is not supported for $vectorSearch: date

    // MongoDB stores DateTimeOffset as UTC BsonDateTime; the offset is lost on round-trip.
    public override Task DateTimeOffset()
        => this.Test<DateTimeOffset>(
            "DateTimeOffset",
            new DateTimeOffset(2020, 1, 1, 12, 30, 45, TimeSpan.Zero),
            new DateTimeOffset(2021, 2, 3, 13, 40, 55, TimeSpan.Zero),
            instantiationExpression: () => new DateTimeOffset(2020, 1, 1, 12, 30, 45, TimeSpan.Zero),
            isFilterable: false); // Operand type is not supported for $vectorSearch: date

#if NET
    public override Task DateOnly()
        => this.Test<DateOnly>(
            "DateOnly",
            new DateOnly(2020, 1, 1),
            new DateOnly(2021, 2, 3),
            isFilterable: false); // Operand type is not supported for $vectorSearch: date
#endif

    public override Task String_array()
        => this.Test<string[]>(
            "StringArray",
            ["foo", "bar"],
            ["foo", "baz"],
            isFilterable: false); // Operand type is not supported for $vectorSearch: array

    public new class Fixture : DataTypeTests<string, DataTypeTests<string>.DefaultRecord>.Fixture
    {
        public override TestStore TestStore => MongoTestStore.Instance;

        // MongoDB does not support null checks in vector search pre-filters
        public override bool IsNullFilteringSupported => false;

        public override Type[] UnsupportedDefaultTypes { get; } =
        [
            typeof(byte),
            typeof(short),
            typeof(Guid),
#if NET
            typeof(TimeOnly)
#endif
        ];
    }
}
