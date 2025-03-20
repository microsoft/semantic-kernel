// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace QdrantIntegrationTests.Support;

public class QdrantUnnamedVectorFixture : VectorStoreFixture
{
    public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;
}
