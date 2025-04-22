// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace QdrantIntegrationTests.Support;

public class QdrantUnnamedSimpleModelFixture : SimpleModelFixture<ulong>
{
    public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;
}
