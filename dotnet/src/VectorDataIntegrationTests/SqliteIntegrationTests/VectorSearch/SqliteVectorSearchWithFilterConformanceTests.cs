// Copyright (c) Microsoft. All rights reserved.

using SqliteIntegrationTests.Support;
using VectorDataSpecificationTests.VectorSearch;
using Xunit;

namespace SqliteIntegrationTests.VectorSearch;

public class SqliteVectorSearchWithFilterConformanceTests(SqliteFixture fixture) :
    VectorSearchWithFilterConformanceTests<string>(fixture),
    IClassFixture<SqliteFixture>
{
}
