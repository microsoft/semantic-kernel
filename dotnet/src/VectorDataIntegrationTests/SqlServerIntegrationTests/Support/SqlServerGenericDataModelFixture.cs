// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace SqlServerIntegrationTests.Support;

public class SqlServerGenericDataModelFixture : GenericDataModelFixture<string>
{
    public override TestStore TestStore => SqlServerTestStore.Instance;
}
