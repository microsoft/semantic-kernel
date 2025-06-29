// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using VectorData.ConformanceTests.CRUD;
using VectorData.ConformanceTests.HybridSearch;
using VectorData.ConformanceTests.VectorSearch;

namespace SqliteVec.ConformanceTests;

public class SqliteTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        typeof(VectorSearchDistanceFunctionComplianceTests<>),
        typeof(DynamicDataModelConformanceTests<>),

        // Hybrid search not supported
        typeof(KeywordVectorizedHybridSearchComplianceTests<>)
    ];
}
