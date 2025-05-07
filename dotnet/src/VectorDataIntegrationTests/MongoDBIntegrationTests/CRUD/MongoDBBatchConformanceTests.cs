// Copyright (c) Microsoft. All rights reserved.

using MongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace MongoDBIntegrationTests.CRUD;

public class MongoDBBatchConformanceTests(MongoDBSimpleModelFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<MongoDBSimpleModelFixture>
{
}
