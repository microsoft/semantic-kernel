// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.Collections;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.Collections;

public class WeaviateCollectionConformanceTests_NamedVectors(WeaviateSimpleModelNamedVectorsFixture fixture)
    : CollectionConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelNamedVectorsFixture>
{
}

public class WeaviateCollectionConformanceTests_UnnamedVector(WeaviateSimpleModelUnnamedVectorFixture fixture)
    : CollectionConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelUnnamedVectorFixture>
{
}
