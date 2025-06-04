// Copyright (c) Microsoft. All rights reserved.

using QdrantIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace QdrantIntegrationTests.CRUD;

public class QdrantRecordConformanceTests_NamedVectors(QdrantNamedSimpleModelFixture fixture)
    : RecordConformanceTests<ulong>(fixture), IClassFixture<QdrantNamedSimpleModelFixture>
{
}

public class QdrantRecordConformanceTests_UnnamedVectors(QdrantUnnamedSimpleModelFixture fixture)
    : RecordConformanceTests<ulong>(fixture), IClassFixture<QdrantUnnamedSimpleModelFixture>
{
}
