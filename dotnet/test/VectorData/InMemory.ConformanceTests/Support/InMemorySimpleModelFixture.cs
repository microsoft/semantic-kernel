// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace InMemory.ConformanceTests.Support;

public class InMemorySimpleModelFixture : SimpleModelFixture<int>
{
    public override TestStore TestStore => InMemoryTestStore.Instance;
}
