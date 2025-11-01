// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests;
using Xunit;

namespace PgVector.ConformanceTests;

public class PostgresCollectionManagementTests(PostgresFixture fixture)
    : CollectionManagementTests<string>(fixture), IClassFixture<PostgresFixture>
{
}
