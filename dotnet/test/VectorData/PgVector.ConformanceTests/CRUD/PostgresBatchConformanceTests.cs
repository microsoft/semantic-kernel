// Copyright (c) Microsoft. All rights reserved.

using PgVectorIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PgVectorIntegrationTests.CRUD;

public class PostgresBatchConformanceTests(PostgresSimpleModelFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<PostgresSimpleModelFixture>
{
}
