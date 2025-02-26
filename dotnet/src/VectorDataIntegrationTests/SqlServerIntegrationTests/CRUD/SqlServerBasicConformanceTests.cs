// Copyright (c) Microsoft. All rights reserved.

using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace SqlServerIntegrationTests.CRUD;

public class SqlServerBasicConformanceTests(SqlServerFixture fixture) : BasicConformanceTests(fixture), IClassFixture<SqlServerFixture>
{
}
