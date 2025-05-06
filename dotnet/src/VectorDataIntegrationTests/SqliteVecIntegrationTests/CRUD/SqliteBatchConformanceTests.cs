// Copyright (c) Microsoft. All rights reserved.

using SqliteVecIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace SqliteVecIntegrationTests.CRUD;

public class SqliteBatchConformanceTests_string(SqliteSimpleModelFixture<string> fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<SqliteSimpleModelFixture<string>>
{
}

public class SqliteBatchConformanceTests_ulong(SqliteSimpleModelFixture<ulong> fixture)
    : BatchConformanceTests<ulong>(fixture), IClassFixture<SqliteSimpleModelFixture<ulong>>
{
}
