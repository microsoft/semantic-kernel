// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using VectorData.ConformanceTests.HybridSearch;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.VectorSearch;

namespace CosmosMongoDB.ConformanceTests;

public class CosmosMongoTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        typeof(VectorSearchDistanceFunctionComplianceTests<>),
        typeof(VectorSearchWithFilterConformanceTests<>),
        typeof(DynamicModelTests<>),

        // Hybrid search not supported
        typeof(KeywordVectorizedHybridSearchComplianceTests<>),
    ];
}
