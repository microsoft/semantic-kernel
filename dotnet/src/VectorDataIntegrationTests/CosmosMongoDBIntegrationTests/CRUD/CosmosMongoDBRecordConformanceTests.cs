// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace CosmosMongoDBIntegrationTests.CRUD;

public class CosmosMongoDBRecordConformanceTests(CosmosMongoSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<CosmosMongoSimpleModelFixture>
{
}
