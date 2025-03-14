// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace PostgresIntegrationTests.Support;

public class PostgresSimpleModelFixture : SimpleModelFixture<string>
{
    public override TestStore TestStore => PostgresTestStore.Instance;
}
