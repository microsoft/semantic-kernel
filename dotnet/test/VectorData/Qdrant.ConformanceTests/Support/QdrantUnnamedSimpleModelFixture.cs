// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace Qdrant.ConformanceTests.Support;

public class QdrantUnnamedSimpleModelFixture : SimpleModelFixture<ulong>
{
    public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;
}
