// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace Qdrant.ConformanceTests.Support;

public class QdrantNamedDynamicDataModelFixture : DynamicDataModelFixture<ulong>
{
    public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
}
