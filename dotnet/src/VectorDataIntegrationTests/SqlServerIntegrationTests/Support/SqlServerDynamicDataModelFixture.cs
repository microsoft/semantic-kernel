// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace SqlServerIntegrationTests.Support;

public class SqlServerDynamicDataModelFixture : DynamicDataModelFixture<string>
{
    public override TestStore TestStore => SqlServerTestStore.Instance;
}
