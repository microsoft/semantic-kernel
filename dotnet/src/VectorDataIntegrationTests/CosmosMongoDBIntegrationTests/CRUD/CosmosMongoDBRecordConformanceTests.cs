// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace CosmosMongoDBIntegrationTests.CRUD;

public class CosmosMongoDBRecordConformanceTests(CosmosMongoDBSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<CosmosMongoDBSimpleModelFixture>
{
}
