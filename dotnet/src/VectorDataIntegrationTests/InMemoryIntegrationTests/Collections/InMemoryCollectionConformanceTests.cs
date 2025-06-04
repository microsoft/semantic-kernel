// Copyright (c) Microsoft. All rights reserved.

using InMemoryIntegrationTests.Support;
using VectorDataSpecificationTests.Collections;
using Xunit;

namespace InMemoryIntegrationTests.Collections;

public class InMemoryCollectionConformanceTests(InMemoryFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<InMemoryFixture>
{
}
