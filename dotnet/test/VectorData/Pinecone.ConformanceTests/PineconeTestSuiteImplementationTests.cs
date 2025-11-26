// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using VectorData.ConformanceTests.ModelTests;

namespace Pinecone.ConformanceTests;

public class PineconeTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        // Pinecone does not support multiple vectors
        typeof(MultiVectorModelTests<>),

        // Hybrid search not supported
        typeof(HybridSearchTests<>)
    ];
}
