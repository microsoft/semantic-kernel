// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Filter;
using Xunit;

namespace SqlServerIntegrationTests.Filter;

public class SqlServerBasicFilterTests(SqlServerFilterFixture fixture) : BasicFilterTestsBase<string>(fixture), IClassFixture<SqlServerFilterFixture>
{
}
