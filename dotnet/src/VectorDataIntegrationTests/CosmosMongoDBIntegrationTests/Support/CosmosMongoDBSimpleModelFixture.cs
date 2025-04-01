// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace CosmosMongoDBIntegrationTests.Support;

public class CosmosMongoDBSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => CosmosMongoDBTestStore.Instance;

    protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.IvfFlat;

    protected override string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;
}
