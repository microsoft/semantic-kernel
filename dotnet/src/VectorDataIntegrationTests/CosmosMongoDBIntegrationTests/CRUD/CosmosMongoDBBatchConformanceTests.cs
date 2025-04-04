// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace CosmosMongoDBIntegrationTests.CRUD;

public class CosmosMongoDBBatchConformanceTests(CosmosMongoDBSimpleModelFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<CosmosMongoDBSimpleModelFixture>
{
}
