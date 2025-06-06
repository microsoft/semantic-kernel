// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.Collections;
using Xunit;

namespace Qdrant.ConformanceTests.Collections;

public class QdrantCollectionConformanceTests_NamedVectors(QdrantNamedVectorsFixture fixture)
    : CollectionConformanceTests<ulong>(fixture), IClassFixture<QdrantNamedVectorsFixture>
{
}

public class QdrantCollectionConformanceTests_UnnamedVector(QdrantUnnamedVectorFixture fixture)
    : CollectionConformanceTests<ulong>(fixture), IClassFixture<QdrantUnnamedVectorFixture>
{
}
