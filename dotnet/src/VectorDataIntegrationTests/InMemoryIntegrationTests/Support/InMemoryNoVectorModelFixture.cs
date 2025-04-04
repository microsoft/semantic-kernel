// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace InMemoryIntegrationTests.Support;

public class InMemoryNoVectorModelFixture : NoVectorModelFixture<string>
{
    public override TestStore TestStore => InMemoryTestStore.Instance;
}
