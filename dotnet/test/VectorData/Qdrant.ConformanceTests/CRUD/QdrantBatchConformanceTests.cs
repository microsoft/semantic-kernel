// Copyright (c) Microsoft. All rights reserved.

using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace QdrantIntegrationTests.CRUD;

public class QdrantBatchConformanceTests_NamedVectors(QdrantNamedSimpleModelFixture fixture)
    : BatchConformanceTests<ulong>(fixture), IClassFixture<QdrantNamedSimpleModelFixture>
{
}

public class QdrantBatchConformanceTests_UnnamedVector(QdrantUnnamedSimpleModelFixture fixture)
    : BatchConformanceTests<ulong>(fixture), IClassFixture<QdrantUnnamedSimpleModelFixture>
{
}
