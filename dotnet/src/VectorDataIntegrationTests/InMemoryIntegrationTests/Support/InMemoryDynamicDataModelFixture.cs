// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace InMemoryIntegrationTests.Support;

public class InMemoryDynamicDataModelFixture : DynamicDataModelFixture<int>
{
    public override TestStore TestStore => InMemoryTestStore.Instance;
}
