// Copyright (c) Microsoft. All rights reserved.

using CosmosNoSQLIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace CosmosNoSQLIntegrationTests.CRUD;

public class CosmosNoSQLNoVectorConformanceTests(CosmosNoSQLNoVectorModelFixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<CosmosNoSQLNoVectorModelFixture>
{
}
