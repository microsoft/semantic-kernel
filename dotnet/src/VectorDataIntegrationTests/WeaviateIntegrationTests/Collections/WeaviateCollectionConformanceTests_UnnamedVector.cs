// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.Collections;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.Collections;

public class WeaviateCollectionConformanceTests_UnnamedVector(WeaviateUnnamedVectorFixture fixture)
    : CollectionConformanceTests<Guid>(fixture), IClassFixture<WeaviateUnnamedVectorFixture>
{
}
