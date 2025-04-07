// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.CRUD;
using VectorDataSpecificationTests.Support;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.CRUD;

public class WeaviateNoVectorConformanceTests(WeaviateNoVectorConformanceTests.Fixture fixture)
    : NoVectorConformanceTests<Guid>(fixture), IClassFixture<WeaviateNoVectorConformanceTests.Fixture>
{
    public new class Fixture : NoVectorConformanceTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.Instance;

        /// <summary>
        /// Weaviate collections must start with an uppercase letter.
        /// </summary>
        protected override string CollectionName => "NoVectorCollection";
    }
}
