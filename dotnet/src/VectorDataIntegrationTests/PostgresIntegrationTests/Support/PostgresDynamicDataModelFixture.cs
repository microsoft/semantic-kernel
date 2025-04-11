// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace PostgresIntegrationTests.Support;

public class PostgresDynamicDataModelFixture : DynamicDataModelFixture<string>
{
    public override TestStore TestStore => PostgresTestStore.Instance;
}
