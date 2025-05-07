// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace QdrantIntegrationTests.Support;

public class QdrantNamedSimpleModelFixture : SimpleModelFixture<ulong>
{
    public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
}
