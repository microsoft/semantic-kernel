// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PostgresIntegrationTests.CRUD;

public class PostgresNoVectorConformanceTests(PostgresNoVectorModelFixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<PostgresNoVectorModelFixture>
{
}
