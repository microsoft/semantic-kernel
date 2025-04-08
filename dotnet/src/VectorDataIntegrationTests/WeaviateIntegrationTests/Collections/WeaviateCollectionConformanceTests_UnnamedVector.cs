// Copyright (c) Microsoft. All rights reserved.

using WeaviateIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace WeaviateIntegrationTests.Collections;

public class WeaviateCollectionConformanceTests_UnnamedVector(WeaviateUnnamedVectorFixture fixture)
    : CollectionConformanceTests<Guid>(fixture), IClassFixture<WeaviateUnnamedVectorFixture>
{
}
