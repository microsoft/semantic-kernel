// Copyright (c) Microsoft. All rights reserved.

using SqliteVec.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace SqliteVec.ConformanceTests.CRUD;

public class SqliteRecordConformanceTests_string(SqliteSimpleModelFixture<string> fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<SqliteSimpleModelFixture<string>>
{
}

public class SqliteRecordConformanceTests_long(SqliteSimpleModelFixture<long> fixture)
    : RecordConformanceTests<long>(fixture), IClassFixture<SqliteSimpleModelFixture<long>>
{
}
