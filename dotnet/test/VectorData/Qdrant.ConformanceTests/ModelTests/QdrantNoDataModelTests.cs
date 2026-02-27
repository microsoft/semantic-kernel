// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Qdrant.ConformanceTests.ModelTests;

public class QdrantNoDataModelTests_NamedVectors(QdrantNoDataModelTests_NamedVectors.Fixture fixture)
    : NoDataModelTests<ulong>(fixture), IClassFixture<QdrantNoDataModelTests_NamedVectors.Fixture>
{
    public new class Fixture : NoDataModelTests<ulong>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }
}

public class QdrantNoDataModelTests_UnnamedVectors(QdrantNoDataModelTests_UnnamedVectors.Fixture fixture)
    : NoDataModelTests<ulong>(fixture), IClassFixture<QdrantNoDataModelTests_UnnamedVectors.Fixture>
{
    public new class Fixture : NoDataModelTests<ulong>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;
    }
}
