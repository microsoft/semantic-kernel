// Copyright (c) Microsoft. All rights reserved.

using MongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.Filter;
using VectorDataSpecificationTests.Support;

namespace MongoDBIntegrationTests.Filter;

public class MongoDBFilterFixture : FilterFixtureBase<string>
{
    protected override TestStore TestStore => MongoDBTestStore.Instance;
}
