// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace QdrantIntegrationTests.Support;

public class QdrantNamedVectorsFixture : VectorStoreFixture
{
    public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
}
