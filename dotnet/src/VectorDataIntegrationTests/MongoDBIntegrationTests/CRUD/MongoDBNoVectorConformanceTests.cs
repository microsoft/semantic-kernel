// Copyright (c) Microsoft. All rights reserved.

using MongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace MongoDBIntegrationTests.CRUD;

public class MongoDBNoVectorConformanceTests(MongoDBNoVectorModelFixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<MongoDBNoVectorModelFixture>
{
}
