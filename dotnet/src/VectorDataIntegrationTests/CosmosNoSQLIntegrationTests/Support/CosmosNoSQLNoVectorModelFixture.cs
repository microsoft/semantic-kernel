// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace CosmosNoSQLIntegrationTests.Support;

public class CosmosNoSQLNoVectorModelFixture : NoVectorModelFixture<string>
{
    public override TestStore TestStore => CosmosNoSqlTestStore.Instance;
}
