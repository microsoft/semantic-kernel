// Copyright (c) Microsoft. All rights reserved.

using InMemory.ConformanceTests.Support;
using VectorData.ConformanceTests;
using Xunit;

namespace InMemory.ConformanceTests;

public class InMemoryCollectionManagementTests(InMemoryFixture fixture)
    : CollectionManagementTests<string>(fixture), IClassFixture<InMemoryFixture>
{
}
