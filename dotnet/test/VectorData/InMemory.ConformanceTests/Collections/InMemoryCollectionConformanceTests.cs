// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests.Collections;
using Xunit;

namespace InMemory.ConformanceTests.Collections;

public class InMemoryCollectionConformanceTests(InMemoryFixture fixture)
    : CollectionConformanceTests<string>(fixture), IClassFixture<InMemoryFixture>
{
}
