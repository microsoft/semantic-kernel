// Copyright (c) Microsoft. All rights reserved.

using SqliteVec.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace SqliteVec.ConformanceTests.CRUD;

public class SqliteBatchConformanceTests_string(SqliteSimpleModelFixture<string> fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<SqliteSimpleModelFixture<string>>
{
}

public class SqliteBatchConformanceTests_long(SqliteSimpleModelFixture<long> fixture)
    : BatchConformanceTests<long>(fixture), IClassFixture<SqliteSimpleModelFixture<long>>
{
}
