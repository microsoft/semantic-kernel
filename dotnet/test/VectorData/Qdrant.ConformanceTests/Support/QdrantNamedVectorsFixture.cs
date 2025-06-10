// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace Qdrant.ConformanceTests.Support;

public class QdrantNamedVectorsFixture : VectorStoreFixture
{
    public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
}
