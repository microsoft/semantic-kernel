// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace CosmosMongoDBIntegrationTests.Support;

public class CosmosMongoDBFixture : VectorStoreFixture
{
    public override TestStore TestStore => CosmosMongoDBTestStore.Instance;
}
