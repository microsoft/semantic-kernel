// Copyright (c) Microsoft. All rights reserved.

using PgVectorIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PgVectorIntegrationTests.CRUD;

public class PostgresRecordConformanceTests(PostgresSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<PostgresSimpleModelFixture>
{
}
