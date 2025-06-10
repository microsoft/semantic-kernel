// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace Qdrant.ConformanceTests.Support;

public class QdrantUnnamedDynamicDataModelFixture : DynamicDataModelFixture<ulong>
{
    public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;
}
