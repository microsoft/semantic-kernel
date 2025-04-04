// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDBIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace CosmosMongoDBIntegrationTests.CRUD;

public class CosmosMongoDBNoVectorConformanceTests(CosmosMongoDBNoVectorModelFixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<CosmosMongoDBNoVectorModelFixture>
{
}
