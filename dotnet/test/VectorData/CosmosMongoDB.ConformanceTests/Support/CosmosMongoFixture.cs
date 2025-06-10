// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace CosmosMongoDB.ConformanceTests.Support;

public class CosmosMongoFixture : VectorStoreFixture
{
    public override TestStore TestStore => CosmosMongoTestStore.Instance;
}
