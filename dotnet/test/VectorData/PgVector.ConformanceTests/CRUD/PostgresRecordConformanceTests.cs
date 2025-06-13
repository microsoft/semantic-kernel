// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace PgVector.ConformanceTests.CRUD;

public class PostgresRecordConformanceTests(PostgresSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<PostgresSimpleModelFixture>
{
}
