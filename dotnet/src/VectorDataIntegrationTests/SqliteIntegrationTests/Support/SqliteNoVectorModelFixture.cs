// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Support;

namespace SqliteIntegrationTests.Support;

public class SqliteNoVectorModelFixture : NoVectorModelFixture<string>
{
    public override TestStore TestStore => SqliteTestStore.Instance;
}
