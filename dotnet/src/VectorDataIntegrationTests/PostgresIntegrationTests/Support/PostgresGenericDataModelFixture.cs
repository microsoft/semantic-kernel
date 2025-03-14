// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace PostgresIntegrationTests.Support;

public class PostgresGenericDataModelFixture : GenericDataModelFixture<string>
{
    public override TestStore TestStore => PostgresTestStore.Instance;
}
