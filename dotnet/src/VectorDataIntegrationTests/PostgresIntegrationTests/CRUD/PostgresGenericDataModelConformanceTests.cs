// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PostgresIntegrationTests.CRUD;

public class PostgresGenericDataModelConformanceTests(PostgresFixture fixture)
    : GenericDataModelConformanceTests<string>(fixture), IClassFixture<PostgresFixture>
{
}
