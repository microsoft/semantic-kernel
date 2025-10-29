// Copyright (c) Microsoft. All rights reserved.

using Pinecone.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Xunit;

namespace Pinecone.ConformanceTests.TypeTests;

public class PineconeDataTypeTests(PineconeDataTypeTests.Fixture fixture)
    : DataTypeTests<string, DataTypeTests<string>.DefaultRecord>(fixture), IClassFixture<PineconeDataTypeTests.Fixture>
{
    public new class Fixture : DataTypeTests<string, DataTypeTests<string>.DefaultRecord>.Fixture
    {
        public override TestStore TestStore => PineconeTestStore.Instance;

        // https://docs.pinecone.io/troubleshooting/restrictions-on-index-names
        public override string CollectionName => "data-type-tests";

        // Pincone does not support null checks in vector search pre-filters
        public override bool IsNullFilteringSupported => false;

        public override Type[] UnsupportedDefaultTypes { get; } =
        [
            typeof(byte),
            typeof(short),
            typeof(decimal),
            typeof(Guid),
            typeof(DateTime),
            typeof(DateTimeOffset),
            typeof(string[]), // TODO: Error with gRPC status code 3

#if NET8_0_OR_GREATER
            typeof(DateOnly),
            typeof(TimeOnly)
#endif
        ];
    }
}
