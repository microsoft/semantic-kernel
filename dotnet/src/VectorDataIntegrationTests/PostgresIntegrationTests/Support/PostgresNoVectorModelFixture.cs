// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace PostgresIntegrationTests.Support;

public class PostgresNoVectorModelFixture : NoVectorModelFixture<string>
{
    public override TestStore TestStore => PostgresTestStore.Instance;
}
