// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using VectorData.ConformanceTests.ModelTests;

namespace CosmosMongoDB.ConformanceTests;

public class CosmosMongoTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        typeof(DynamicModelTests<>),

        // Hybrid search not supported
        typeof(HybridSearchTests<>),
    ];
}
