// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.TypeTests;

public class WeaviateDataTypeTests(WeaviateDataTypeTests.Fixture fixture)
    : DataTypeTests<Guid, DataTypeTests<Guid>.DefaultRecord>(fixture), IClassFixture<WeaviateDataTypeTests.Fixture>
{
    public override Task String_array()
        => this.Test<string[]>(
            "StringArray",
            ["foo", "bar"],
            ["foo", "baz"],
            isFilterable: false); // TODO: We don't currently support filtering on arrays

    public new class Fixture : DataTypeTests<Guid, DataTypeTests<Guid>.DefaultRecord>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;

        // TODO: Weaviate requires special indexing for filtering on nulls, see #10358
        public override bool IsNullFilteringSupported => false;

        public override Type[] UnsupportedDefaultTypes { get; } =
        [
            typeof(DateTime),
#if NET8_0_OR_GREATER
            typeof(DateOnly),
            typeof(TimeOnly)
#endif
        ];
    }
}
