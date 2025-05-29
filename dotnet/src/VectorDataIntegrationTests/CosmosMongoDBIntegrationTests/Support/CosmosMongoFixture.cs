// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace CosmosMongoDBIntegrationTests.Support;

public class CosmosMongoFixture : VectorStoreFixture
{
    public override TestStore TestStore => CosmosMongoTestStore.Instance;
}
