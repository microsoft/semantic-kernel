// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace InMemory.ConformanceTests.Support;

public class InMemoryFixture : VectorStoreFixture
{
    public override TestStore TestStore => InMemoryTestStore.Instance;
}
