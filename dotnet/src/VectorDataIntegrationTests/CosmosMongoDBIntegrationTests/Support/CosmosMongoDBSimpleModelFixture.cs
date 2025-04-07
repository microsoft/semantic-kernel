// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace CosmosMongoDBIntegrationTests.Support;

public class CosmosMongoDBSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => CosmosMongoDBTestStore.Instance;
}
