// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace SqlServerIntegrationTests.Support;

public class SqlServerNoVectorModelFixture : NoVectorModelFixture<string>
{
    public override TestStore TestStore => SqlServerTestStore.Instance;
}
