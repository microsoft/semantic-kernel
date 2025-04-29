// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace CosmosNoSQLIntegrationTests.Support;

public class CosmosNoSQLFixture : VectorStoreFixture
{
    public override TestStore TestStore => CosmosNoSQLTestStore.Instance;
}
