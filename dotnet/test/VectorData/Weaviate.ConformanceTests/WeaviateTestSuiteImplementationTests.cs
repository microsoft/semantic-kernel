// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using VectorData.ConformanceTests.VectorSearch;

namespace Weaviate.ConformanceTests;

public class WeaviateTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        typeof(VectorSearchWithFilterConformanceTests<>)
    ];
}
