// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using VectorData.ConformanceTests.HybridSearch;
using VectorData.ConformanceTests.ModelTests;

namespace SqliteVec.ConformanceTests;

public class SqliteTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        typeof(DynamicModelTests<>),

        // Hybrid search not supported
        typeof(KeywordVectorizedHybridSearchComplianceTests<>)
    ];
}
