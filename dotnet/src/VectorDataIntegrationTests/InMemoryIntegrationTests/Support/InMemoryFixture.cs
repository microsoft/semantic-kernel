// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace InMemoryIntegrationTests.Support;

public class InMemoryFixture : VectorStoreFixture
{
    public override TestStore TestStore => InMemoryTestStore.Instance;
}
