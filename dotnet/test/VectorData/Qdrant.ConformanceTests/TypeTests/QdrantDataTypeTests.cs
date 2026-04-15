// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Xunit;

namespace Qdrant.ConformanceTests.TypeTests;

public class QdrantDataTypeTests(QdrantDataTypeTests.Fixture fixture)
    : DataTypeTests<Guid, DataTypeTests<Guid>.DefaultRecord>(fixture), IClassFixture<QdrantDataTypeTests.Fixture>
{
    // Qdrant doesn't seem to support filtering on float/double or string ararys,
    // https://qdrant.tech/documentation/concepts/filtering/#match
    [Fact]
    public override Task Float()
        => this.Test<float>("Float", 8.5f, 9.5f, isFilterable: false);

    [Fact]
    public override Task Double()
        => this.Test<double>("Double", 8.5d, 9.5d, isFilterable: false);

    [Fact]
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
#if NET
            typeof(TimeOnly)
#endif
        ];
    }
}
