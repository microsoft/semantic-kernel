// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace SqliteIntegrationTests.Support;

public class SqliteFixture : VectorStoreFixture
{
    public override TestStore TestStore => SqliteTestStore.Instance;
}
