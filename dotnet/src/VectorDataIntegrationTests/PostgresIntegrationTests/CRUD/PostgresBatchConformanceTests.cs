// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PostgresIntegrationTests.CRUD;

public class PostgresBatchConformanceTests(PostgresSimpleModelFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<PostgresSimpleModelFixture>
{
}
