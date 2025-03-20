﻿// Copyright (c) Microsoft. All rights reserved.

using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace QdrantIntegrationTests.Filter;

public class QdrantBasicFilterTests(QdrantBasicFilterTests.Fixture fixture)
    : BasicFilterTests<ulong>(fixture), IClassFixture<QdrantBasicFilterTests.Fixture>
{
    public new class Fixture : BasicFilterTests<ulong>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;

        // Qdrant doesn't support the default Flat index kind
        protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.Hnsw;
    }
}
