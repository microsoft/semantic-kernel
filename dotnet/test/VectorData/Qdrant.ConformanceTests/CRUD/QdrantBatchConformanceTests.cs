// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace Qdrant.ConformanceTests.CRUD;

public class QdrantBatchConformanceTests_NamedVectors(QdrantNamedSimpleModelFixture fixture)
    : BatchConformanceTests<ulong>(fixture), IClassFixture<QdrantNamedSimpleModelFixture>
{
}

public class QdrantBatchConformanceTests_UnnamedVector(QdrantUnnamedSimpleModelFixture fixture)
    : BatchConformanceTests<ulong>(fixture), IClassFixture<QdrantUnnamedSimpleModelFixture>
{
}
