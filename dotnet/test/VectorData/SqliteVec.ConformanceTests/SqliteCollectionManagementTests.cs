// Copyright (c) Microsoft. All rights reserved.

using SqliteVec.ConformanceTests.Support;
using VectorData.ConformanceTests;
using Xunit;

namespace SqliteVec.ConformanceTests;

public class SqliteCollectionManagementTests(SqliteFixture fixture)
    : CollectionManagementTests<string>(fixture), IClassFixture<SqliteFixture>
{
}
