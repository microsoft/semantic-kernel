// Copyright (c) Microsoft. All rights reserved.

using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace QdrantIntegrationTests.Filter;

public class QdrantBasicQueryTests(QdrantBasicQueryTests.Fixture fixture)
    : BasicQueryTests<ulong>(fixture), IClassFixture<QdrantBasicQueryTests.Fixture>
{
    public new class Fixture : BasicQueryTests<ulong>.QueryFixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;

        // Qdrant doesn't support the default Flat index kind
        protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.Hnsw;
    }
}
