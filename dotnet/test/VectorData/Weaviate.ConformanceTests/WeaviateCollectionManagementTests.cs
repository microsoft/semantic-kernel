// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests;

public class WeaviateCollectionManagementTests_NamedVectors(WeaviateSimpleModelNamedVectorsFixture fixture)
    : CollectionManagementTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelNamedVectorsFixture>
{
}

public class WeaviateCollectionManagementTests_UnnamedVector(WeaviateSimpleModelUnnamedVectorFixture fixture)
    : CollectionManagementTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelUnnamedVectorFixture>
{
}
