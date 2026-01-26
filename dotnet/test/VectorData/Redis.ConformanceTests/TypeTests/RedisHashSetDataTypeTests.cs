// Copyright (c) Microsoft. All rights reserved.

using Redis.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Xunit;

namespace Redis.ConformanceTests.TypeTests;

public class RedisHashSetDataTypeTests(RedisHashSetDataTypeTests.Fixture fixture)
    : DataTypeTests<string, DataTypeTests<string>.DefaultRecord>(fixture), IClassFixture<RedisHashSetDataTypeTests.Fixture>
{
    public override Task Bool() => Task.CompletedTask;
    public override Task Decimal() => Task.CompletedTask;
    public override Task DateTime() => Task.CompletedTask;
    public override Task DateTimeOffset() => Task.CompletedTask;
    public override Task DateOnly() => Task.CompletedTask;
    public override Task TimeOnly() => Task.CompletedTask;

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
#if NET
            typeof(DateOnly),
            typeof(TimeOnly)
#endif
        ];
    }
}
