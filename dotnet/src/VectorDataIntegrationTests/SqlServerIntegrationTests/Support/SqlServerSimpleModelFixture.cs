// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace SqlServerIntegrationTests.Support;

public class SqlServerSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => SqlServerTestStore.Instance;
}
