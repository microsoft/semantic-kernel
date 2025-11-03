// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using VectorData.ConformanceTests.HybridSearch;

namespace InMemory.ConformanceTests;

public class InMemoryTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        typeof(DependencyInjectionTests<,,,>),
        typeof(DependencyInjectionTests<>),

        // Hybrid search not supported
        typeof(KeywordVectorizedHybridSearchComplianceTests<>)
    ];
}
