// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace Qdrant.ConformanceTests.CRUD;

public class QdrantRecordConformanceTests_NamedVectors(QdrantNamedSimpleModelFixture fixture)
    : RecordConformanceTests<ulong>(fixture), IClassFixture<QdrantNamedSimpleModelFixture>
{
}

public class QdrantRecordConformanceTests_UnnamedVectors(QdrantUnnamedSimpleModelFixture fixture)
    : RecordConformanceTests<ulong>(fixture), IClassFixture<QdrantUnnamedSimpleModelFixture>
{
}
