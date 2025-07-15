// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using VectorData.ConformanceTests.CRUD;
using VectorData.ConformanceTests.VectorSearch;

namespace CosmosNoSql.ConformanceTests;

public class CosmosNoSqlTestSuiteImplementationTests : TestSuiteImplementationTests
{
    protected override ICollection<Type> IgnoredTestBases { get; } =
    [
        typeof(VectorSearchDistanceFunctionComplianceTests<>),
        typeof(VectorSearchWithFilterConformanceTests<>),
        typeof(DynamicDataModelConformanceTests<>),
        typeof(BatchConformanceTests<>)
    ];
}
