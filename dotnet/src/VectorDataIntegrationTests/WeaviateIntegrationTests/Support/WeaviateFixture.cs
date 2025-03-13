// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace WeaviateIntegrationTests.Support;

public class WeaviateFixture : VectorStoreFixture
{
    public override TestStore TestStore => WeaviateTestStore.Instance;

    // Weaviate requires the name to start with a capital letter and not contain any chars other than a-Z and 0-9.
    public override string GetUniqueCollectionName() => $"A{Guid.NewGuid():N}";
}
