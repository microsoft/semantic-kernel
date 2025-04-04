// Copyright (c) Microsoft. All rights reserved.

using SqliteIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace SqliteIntegrationTests.CRUD;

public class SqliteNoVectorConformanceTests(SqliteNoVectorModelFixture fixture)
    : NoVectorConformanceTests<string>(fixture), IClassFixture<SqliteNoVectorModelFixture>
{
}
