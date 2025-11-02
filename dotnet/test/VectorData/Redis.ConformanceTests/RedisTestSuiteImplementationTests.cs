// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using VectorData.ConformanceTests.HybridSearch;

namespace Redis.ConformanceTests;

public class RedisTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        // Hybrid search not supported
        typeof(KeywordVectorizedHybridSearchComplianceTests<>)
    ];
}
