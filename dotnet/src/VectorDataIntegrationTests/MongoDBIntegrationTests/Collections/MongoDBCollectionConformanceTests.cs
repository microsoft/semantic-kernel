// Copyright (c) Microsoft. All rights reserved.

using MongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace MongoDBIntegrationTests.Collections;

public class MongoDBCollectionConformanceTests(MongoDBFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<MongoDBFixture>
{
}
