// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Support;

namespace SqlServer.ConformanceTests.Support;

public class SqlServerSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => SqlServerTestStore.Instance;
}
