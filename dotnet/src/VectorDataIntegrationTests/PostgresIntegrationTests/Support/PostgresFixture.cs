// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace PostgresIntegrationTests.Support;

public class PostgresFixture : VectorStoreFixture
{
    public override TestStore TestStore => PostgresTestStore.Instance;
}
