// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.CRUD;
using VectorData.ConformanceTests.Support;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.CRUD;

public class WeaviateNoDataConformanceTests_NamedVectors(WeaviateNoDataConformanceTests_NamedVectors.Fixture fixture)
    : NoDataConformanceTests<Guid>(fixture), IClassFixture<WeaviateNoDataConformanceTests_NamedVectors.Fixture>
{
    public new class Fixture : NoDataConformanceTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;

        /// <summary>
        /// Weaviate collections must start with an uppercase letter.
        /// </summary>
        public override string CollectionName => "NoDataNamedCollection";
    }
}

public class WeaviateNoDataConformanceTests_UnnamedVector(WeaviateNoDataConformanceTests_UnnamedVector.Fixture fixture)
    : NoDataConformanceTests<Guid>(fixture), IClassFixture<WeaviateNoDataConformanceTests_UnnamedVector.Fixture>
{
    public new class Fixture : NoDataConformanceTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.UnnamedVectorInstance;

        /// <summary>
        /// Weaviate collections must start with an uppercase letter.
        /// </summary>
        public override string CollectionName => "NoDataUnnamedCollection";
    }
}
