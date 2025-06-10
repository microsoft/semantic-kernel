// Copyright (c) Microsoft. All rights reserved.

using PgVector.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace PgVector.ConformanceTests.CRUD;

public class PostgresDynamicDataModelConformanceTests(PostgresDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<string>(fixture), IClassFixture<PostgresDynamicDataModelFixture>
{
}
