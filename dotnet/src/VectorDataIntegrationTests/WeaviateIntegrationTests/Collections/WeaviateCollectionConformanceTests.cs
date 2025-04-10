// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Collections;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.Collections;

public class WeaviateCollectionConformanceTests_NamedVectors(WeaviateSimpleModelNamedVectorsFixture fixture)
    : CollectionConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelNamedVectorsFixture>
{
}

public class WeaviateCollectionConformanceTests_UnnamedVector(WeaviateSimpleModelUnnamedVectorFixture fixture)
    : CollectionConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelUnnamedVectorFixture>
{
}
