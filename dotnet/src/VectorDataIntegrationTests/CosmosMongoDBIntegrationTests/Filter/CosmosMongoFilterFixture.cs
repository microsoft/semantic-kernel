// Copyright (c) Microsoft. All rights reserved.

using MongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;

namespace MongoDBIntegrationTests.Filter;

public class CosmosMongoFilterFixture : FilterFixtureBase<string>
{
    protected override TestStore TestStore => CosmosMongoDBTestStore.Instance;

    protected override string IndexKind => Microsoft.Extensions.VectorData.IndexKind.IvfFlat;
    protected override string DistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;
}
