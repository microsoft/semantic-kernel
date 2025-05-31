// Copyright (c) Microsoft. All rights reserved.

using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace SqlServerIntegrationTests.Collections;

public class SqlServerCollectionConformanceTests(SqlServerFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<SqlServerFixture>
{
}
