// Copyright (c) Microsoft. All rights reserved.

using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace SqlServer.ConformanceTests.CRUD;

public class SqlServerDynamicDataModelConformanceTests(SqlServerDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<string>(fixture), IClassFixture<SqlServerDynamicDataModelFixture>
{
}
