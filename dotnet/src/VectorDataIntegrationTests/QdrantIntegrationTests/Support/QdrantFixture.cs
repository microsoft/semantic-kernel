// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace QdrantIntegrationTests.Support;

public class QdrantFixture : VectorStoreFixture
{
    public override TestStore TestStore => QdrantTestStore.Instance;
}
