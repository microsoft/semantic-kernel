// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;

namespace PgVector.ConformanceTests;

public class PostgresTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        // Hybrid search not supported
        typeof(HybridSearchTests<>)
    ];
}
