// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace CosmosNoSqlIntegrationTests.Support;

public class CosmosNoSqlFixture : VectorStoreFixture
{
    public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
}
