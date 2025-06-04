// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace SqlServerIntegrationTests.Support;

public class SqlServerFixture : VectorStoreFixture
{
    public override TestStore TestStore => SqlServerTestStore.Instance;
}
