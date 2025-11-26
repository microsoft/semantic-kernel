// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace Qdrant.ConformanceTests.TypeTests;

public class QdrantDataTypeTests(QdrantDataTypeTests.Fixture fixture)
    : DataTypeTests<Guid, DataTypeTests<Guid>.DefaultRecord>(fixture), IClassFixture<QdrantDataTypeTests.Fixture>
{
    // Qdrant doesn't seem to support filtering on float/double or string ararys,
    // https://qdrant.tech/documentation/concepts/filtering/#match
    [ConditionalFact]
    public override Task Float()
        => this.Test<float>("Float", 8.5f, 9.5f, isFilterable: false);

    [ConditionalFact]
    public override Task Double()
        => this.Test<double>("Double", 8.5d, 9.5d, isFilterable: false);

    [ConditionalFact]
    public override Task String_array()
        => this.Test<string[]>(
            "StringArray",
            ["foo", "bar"],
            ["foo", "baz"],
            isFilterable: false);

    public new class Fixture : DataTypeTests<Guid, DataTypeTests<Guid>.DefaultRecord>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;

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
