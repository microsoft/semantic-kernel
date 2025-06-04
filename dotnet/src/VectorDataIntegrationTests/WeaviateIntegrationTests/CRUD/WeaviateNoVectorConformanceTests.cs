// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.CRUD;

public class WeaviateNoVectorConformanceTests_NamedVectors(WeaviateNoVectorConformanceTests_NamedVectors.Fixture fixture)
    : NoVectorConformanceTests<Guid>(fixture), IClassFixture<WeaviateNoVectorConformanceTests_NamedVectors.Fixture>
{
    public new class Fixture : NoVectorConformanceTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;

        /// <summary>
        /// Weaviate collections must start with an uppercase letter.
        /// </summary>
        public override string CollectionName => "NoVectorNamedCollection";
    }
}
