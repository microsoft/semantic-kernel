// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;

namespace InMemory.ConformanceTests;

public class InMemoryTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        typeof(DependencyInjectionTests<,,,>),
        typeof(DependencyInjectionTests<>),

        // Hybrid search not supported
        typeof(HybridSearchTests<>)
    ];
}
