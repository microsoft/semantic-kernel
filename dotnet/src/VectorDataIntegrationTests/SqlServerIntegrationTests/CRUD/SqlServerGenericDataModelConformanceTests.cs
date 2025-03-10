// Copyright (c) Microsoft. All rights reserved.

using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace SqlServerIntegrationTests.CRUD;

public class SqlServerGenericDataModelConformanceTests(SqlServerFixture fixture)
    : GenericDataModelConformanceTests<string>(fixture), IClassFixture<SqlServerFixture>
{
}
