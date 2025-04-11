// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.CRUD;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.CRUD;

public class WeaviateRecordConformanceTests_NamedVectors(WeaviateSimpleModelNamedVectorsFixture fixture)
    : RecordConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelNamedVectorsFixture>
{
}

public class WeaviateRecordConformanceTests_UnnamedVector(WeaviateSimpleModelUnnamedVectorFixture fixture)
    : RecordConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelUnnamedVectorFixture>
{
}
