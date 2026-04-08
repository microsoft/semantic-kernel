// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.TypeTests;
using Xunit;

namespace InMemory.ConformanceTests.TypeTests;

public class InMemoryDataTypeTests(InMemoryDataTypeTests.Fixture fixture)
    : DataTypeTests<string, DataTypeTests<string>.DefaultRecord>(fixture), IClassFixture<InMemoryDataTypeTests.Fixture>
{
    public new class Fixture : DataTypeTests<string, DataTypeTests<string>.DefaultRecord>.Fixture
    {
        public override TestStore TestStore => InMemoryTestStore.Instance;

        public override Type[] UnsupportedDefaultTypes { get; } = [];
    }
}
