// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace CosmosMongoDBIntegrationTests.CRUD;

public class CosmosMongoDBBatchConformanceTests(CosmosMongoSimpleModelFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<CosmosMongoSimpleModelFixture>
{
}
