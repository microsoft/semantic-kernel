// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace InMemoryIntegrationTests.Support;

public class InMemorySimpleModelFixture : SimpleModelFixture<int>
{
    public override TestStore TestStore => InMemoryTestStore.Instance;
}
