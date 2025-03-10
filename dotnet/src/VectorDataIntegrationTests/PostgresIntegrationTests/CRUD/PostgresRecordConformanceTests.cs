// Copyright (c) Microsoft. All rights reserved.

using PostgresIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PostgresIntegrationTests.CRUD;

public class PostgresRecordConformanceTests(PostgresFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<PostgresFixture>
{
}
