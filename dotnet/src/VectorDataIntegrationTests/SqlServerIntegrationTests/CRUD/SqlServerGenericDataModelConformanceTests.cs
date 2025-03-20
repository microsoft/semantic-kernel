// Copyright (c) Microsoft. All rights reserved.

using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace SqlServerIntegrationTests.CRUD;

public class SqlServerGenericDataModelConformanceTests(SqlServerGenericDataModelFixture fixture)
    : GenericDataModelConformanceTests<string>(fixture), IClassFixture<SqlServerGenericDataModelFixture>
{
}
