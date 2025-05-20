// Copyright (c) Microsoft. All rights reserved.

using PgVectorIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PgVectorIntegrationTests.CRUD;

public class PostgresDynamicDataModelConformanceTests(PostgresDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<string>(fixture), IClassFixture<PostgresDynamicDataModelFixture>
{
}
