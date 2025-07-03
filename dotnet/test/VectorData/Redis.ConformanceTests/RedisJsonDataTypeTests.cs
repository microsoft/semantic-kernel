// Copyright (c) Microsoft. All rights reserved.

using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Redis.ConformanceTests;

public class RedisJsonDataTypeTests(RedisJsonDataTypeTests.Fixture fixture)
    : DataTypeTests<string, DataTypeTests<string>.DefaultRecord>(fixture), IClassFixture<RedisJsonDataTypeTests.Fixture>
{
    public override Task String_array()
        => this.Test<string[]>(
            "StringArray",
            ["foo", "bar"],
            ["foo", "baz"],
            isFilterable: false);

    public new class Fixture : DataTypeTests<string, DataTypeTests<string>.DefaultRecord>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.JsonInstance;

        public override bool IsNullSupported => false;
        public override bool IsNullFilteringSupported => false;

        public override Type[] UnsupportedDefaultTypes { get; } =
        [
            typeof(bool),
            typeof(decimal),
            typeof(Guid),
            typeof(DateTime),
            typeof(DateTimeOffset),
#if NET8_0_OR_GREATER
            typeof(DateOnly),
            typeof(TimeOnly)
#endif
        ];
    }
}
