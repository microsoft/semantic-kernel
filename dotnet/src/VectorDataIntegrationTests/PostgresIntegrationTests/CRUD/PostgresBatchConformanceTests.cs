// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PostgresIntegrationTests.CRUD;

public class PostgresBatchConformanceTests(PostgresFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<PostgresFixture>
{
}
