// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace SqlServer.ConformanceTests.Support;

public class SqlServerFixture : VectorStoreFixture
{
    public override TestStore TestStore => SqlServerTestStore.Instance;
}
