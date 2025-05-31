// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace WeaviateIntegrationTests.Support;

public class WeaviateDynamicDataModelFixture : DynamicDataModelFixture<Guid>
{
    public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;

    // Weaviate requires the name to start with a capital letter and not contain any chars other than a-Z and 0-9.
    // Source: https://weaviate.io/developers/weaviate/starter-guides/managing-collections#collection--property-names
    public override string CollectionName => this.GetUniqueCollectionName();

    public override string GetUniqueCollectionName() => $"A{Guid.NewGuid():N}";
}

public class WeaviateDynamicDataModelNamedVectorsFixture : WeaviateDynamicDataModelFixture
{
    public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
}

public class WeaviateDynamicDataModelUnnamedVectorFixture : WeaviateDynamicDataModelFixture
{
    public override TestStore TestStore => WeaviateTestStore.UnnamedVectorInstance;
}
