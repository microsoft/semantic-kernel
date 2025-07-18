// Copyright (c) Microsoft. All rights reserved.

using SqlServer.ConformanceTests.Support;
using VectorData.ConformanceTests.Collections;
using Xunit;

namespace SqlServer.ConformanceTests.Collections;

public class SqlServerCollectionConformanceTests(SqlServerFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<SqlServerFixture>
{
}
