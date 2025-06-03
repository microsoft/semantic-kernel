// Copyright (c) Microsoft. All rights reserved.

using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace QdrantIntegrationTests.CRUD;

public class QdrantDynamicDataModelConformanceTests_NamedVectors(QdrantNamedDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<ulong>(fixture), IClassFixture<QdrantNamedDynamicDataModelFixture>
{
}

public class QdrantDynamicDataModelConformanceTests_UnnamedVector(QdrantUnnamedDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<ulong>(fixture), IClassFixture<QdrantUnnamedDynamicDataModelFixture>
{
}
