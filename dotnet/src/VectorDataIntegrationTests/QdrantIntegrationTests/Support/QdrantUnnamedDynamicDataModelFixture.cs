// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace QdrantIntegrationTests.Support;

public class QdrantUnnamedDynamicDataModelFixture : DynamicDataModelFixture<ulong>
{
    public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;
}
