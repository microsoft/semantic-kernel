// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using VectorData.ConformanceTests.VectorSearch;

namespace Qdrant.ConformanceTests;

public class QdrantTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        typeof(VectorSearchDistanceFunctionComplianceTests<>),
        typeof(VectorSearchWithFilterConformanceTests<>)
    ];
}
