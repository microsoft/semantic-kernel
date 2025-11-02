// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using VectorData.ConformanceTests.HybridSearch;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.VectorSearch;

namespace Pinecone.ConformanceTests;

public class PineconeTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        typeof(VectorSearchWithFilterConformanceTests<>),

        // Pinecone does not support multiple vectors
        typeof(MultiVectorModelTests<>),

        // Hybrid search not supported
        typeof(KeywordVectorizedHybridSearchComplianceTests<>)
    ];
}
