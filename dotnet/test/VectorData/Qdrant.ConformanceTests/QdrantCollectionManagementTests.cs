// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests;
using Xunit;

namespace Qdrant.ConformanceTests;

public class QdrantCollectionManagementTests_NamedVectors(QdrantNamedVectorsFixture fixture)
    : CollectionManagementTests<ulong>(fixture), IClassFixture<QdrantNamedVectorsFixture>
{
}

public class QdrantCollectionManagementTests_UnnamedVector(QdrantUnnamedVectorFixture fixture)
    : CollectionManagementTests<ulong>(fixture), IClassFixture<QdrantUnnamedVectorFixture>
{
}
