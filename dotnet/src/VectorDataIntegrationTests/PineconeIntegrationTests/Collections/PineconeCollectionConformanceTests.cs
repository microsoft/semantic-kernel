// Copyright (c) Microsoft. All rights reserved.

using PineconeIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace PineconeIntegrationTests.Collections;

public class PineconeCollectionConformanceTests(PineconeFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<PineconeFixture>
{
}
