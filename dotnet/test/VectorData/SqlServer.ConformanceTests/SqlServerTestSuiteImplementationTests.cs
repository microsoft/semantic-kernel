// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;

namespace SqlServer.ConformanceTests;

public class SqlServerTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        // Hybrid search not supported
        typeof(HybridSearchTests<>)
    ];
}
