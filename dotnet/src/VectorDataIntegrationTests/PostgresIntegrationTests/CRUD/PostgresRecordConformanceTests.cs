// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PostgresIntegrationTests.CRUD;

public class PostgresRecordConformanceTests(PostgresSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<PostgresSimpleModelFixture>
{
}
