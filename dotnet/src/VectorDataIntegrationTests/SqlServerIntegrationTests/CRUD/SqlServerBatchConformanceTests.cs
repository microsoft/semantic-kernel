﻿// Copyright (c) Microsoft. All rights reserved.

using SqlServerIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace SqlServerIntegrationTests.CRUD;

public class SqlServerBatchConformanceTests(SqlServerSimpleModelFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<SqlServerSimpleModelFixture>
{
}
