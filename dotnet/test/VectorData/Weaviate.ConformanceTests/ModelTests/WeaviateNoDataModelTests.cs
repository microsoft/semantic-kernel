// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.ModelTests;

public class WeaviateNoDataModelTests_NamedVectors(WeaviateNoDataModelTests_NamedVectors.Fixture fixture)
    : NoDataModelTests<Guid>(fixture), IClassFixture<WeaviateNoDataModelTests_NamedVectors.Fixture>
{
    public new class Fixture : NoDataModelTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;

        /// <summary>
        /// Weaviate collections must start with an uppercase letter.
        /// </summary>
        protected override string CollectionNameBase => "NoDataNamedCollection";
    }
}

public class WeaviateNoDataModelTests_UnnamedVector(WeaviateNoDataModelTests_UnnamedVector.Fixture fixture)
    : NoDataModelTests<Guid>(fixture), IClassFixture<WeaviateNoDataModelTests_UnnamedVector.Fixture>
{
    public new class Fixture : NoDataModelTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.UnnamedVectorInstance;

        /// <summary>
        /// Weaviate collections must start with an uppercase letter.
        /// </summary>
        protected override string CollectionNameBase => "NoDataUnnamedCollection";
    }
}
