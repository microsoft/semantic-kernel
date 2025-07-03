// Copyright (c) Microsoft. All rights reserved.

using MongoDB.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace MongoDB.ConformanceTests;

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
            typeof(DateTimeOffset),
#if NET8_0_OR_GREATER
            typeof(DateOnly),
            typeof(TimeOnly)
#endif
        ];
    }
}
