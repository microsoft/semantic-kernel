// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace QdrantIntegrationTests.Support;

public class QdrantNamedDynamicDataModelFixture : DynamicDataModelFixture<ulong>
{
    public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
}
