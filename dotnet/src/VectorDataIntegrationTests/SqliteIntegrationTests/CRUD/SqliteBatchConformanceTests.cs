// Copyright (c) Microsoft. All rights reserved.

using SqliteIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace SqliteIntegrationTests.CRUD;

public class SqliteBatchConformanceTests_string(SqliteSimpleModelFixture<string> fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<SqliteSimpleModelFixture<string>>
{
}

public class SqliteBatchConformanceTests_ulong(SqliteSimpleModelFixture<ulong> fixture)
    : BatchConformanceTests<ulong>(fixture), IClassFixture<SqliteSimpleModelFixture<ulong>>
{
}
