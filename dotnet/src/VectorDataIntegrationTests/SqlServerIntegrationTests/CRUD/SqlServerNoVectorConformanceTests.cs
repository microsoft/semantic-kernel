// Copyright (c) Microsoft. All rights reserved.

using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace SqlServerIntegrationTests.CRUD;

public class SqlServerNoVectorConformanceTests(SqlServerNoVectorModelFixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<SqlServerNoVectorModelFixture>
{
}
