// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PostgresIntegrationTests.CRUD;

public class PostgresDynamicDataModelConformanceTests(PostgresDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<string>(fixture), IClassFixture<PostgresDynamicDataModelFixture>
{
}
