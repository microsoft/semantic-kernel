// Copyright (c) Microsoft. All rights reserved.

using SqliteIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace SqliteIntegrationTests.Collections;

public class SqliteCollectionConformanceTests(SqliteFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<SqliteFixture>
{
}
