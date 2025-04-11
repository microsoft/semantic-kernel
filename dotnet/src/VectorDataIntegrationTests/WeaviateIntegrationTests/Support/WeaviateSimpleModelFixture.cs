// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace WeaviateIntegrationTests.Support;

public class WeaviateSimpleModelFixture : SimpleModelFixture<Guid>
{
    public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;

    protected override string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;

    // Weaviate requires the name to start with a capital letter and not contain any chars other than a-Z and 0-9.
    // Source: https://weaviate.io/developers/weaviate/starter-guides/managing-collections#collection--property-names
    protected override string CollectionName => this.GetUniqueCollectionName();

    public override string GetUniqueCollectionName() => $"A{Guid.NewGuid():N}";
}

public class WeaviateSimpleModelNamedVectorsFixture : WeaviateSimpleModelFixture
{
    public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
}

public class WeaviateSimpleModelUnnamedVectorFixture : WeaviateSimpleModelFixture
{
    public override TestStore TestStore => WeaviateTestStore.UnnamedVectorInstance;
}
