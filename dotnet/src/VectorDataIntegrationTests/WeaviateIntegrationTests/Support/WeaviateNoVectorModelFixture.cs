// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace WeaviateIntegrationTests.Support;

public class WeaviateNoVectorModelFixture : NoVectorModelFixture<Guid>
{
    public override TestStore TestStore => WeaviateTestStore.Instance;

    /// <summary>
    /// Weaviate collections must start with an uppercase letter.
    /// </summary>
    protected override string CollectionName => "NoVectorCollection";
}
