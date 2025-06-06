// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace CosmosNoSql.ConformanceTests.Support;

public class CosmosNoSqlFixture : VectorStoreFixture
{
    public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
}
