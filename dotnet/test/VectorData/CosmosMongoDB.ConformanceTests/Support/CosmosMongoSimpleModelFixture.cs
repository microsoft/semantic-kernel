// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace CosmosMongoDBIntegrationTests.Support;

public class CosmosMongoSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => CosmosMongoTestStore.Instance;
}
