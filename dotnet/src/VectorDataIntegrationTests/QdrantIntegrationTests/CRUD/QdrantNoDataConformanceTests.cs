// Copyright (c) Microsoft. All rights reserved.

using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace QdrantIntegrationTests.CRUD;

public class QdrantNoDataConformanceTests_NamedVectors(QdrantNoDataConformanceTests_NamedVectors.Fixture fixture)
    : NoDataConformanceTests<ulong>(fixture), IClassFixture<QdrantNoDataConformanceTests_NamedVectors.Fixture>
{
    public new class Fixture : NoDataConformanceTests<ulong>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }
}

public class QdrantNoDataConformanceTests_UnnamedVectors(QdrantNoDataConformanceTests_UnnamedVectors.Fixture fixture)
    : NoDataConformanceTests<ulong>(fixture), IClassFixture<QdrantNoDataConformanceTests_UnnamedVectors.Fixture>
{
    public new class Fixture : NoDataConformanceTests<ulong>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;
    }
}
