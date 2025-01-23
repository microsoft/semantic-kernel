// Copyright (c) Microsoft. All rights reserved.

using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;

namespace QdrantIntegrationTests.Filter;

public class QdrantFilterFixture : FilterFixtureBase<ulong>
{
    protected override TestStore TestStore => QdrantTestStore.Instance;

    // Qdrant doesn't support the default Flat index kind
    protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.Hnsw;
}
