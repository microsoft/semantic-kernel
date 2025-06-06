// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace PgVector.ConformanceTests.CRUD;

public class PostgresBatchConformanceTests(PostgresSimpleModelFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<PostgresSimpleModelFixture>
{
}
