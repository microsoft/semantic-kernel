// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.CRUD;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.CRUD;

public class WeaviateDynamicRecordConformanceTests_NamedVectors(WeaviateDynamicDataModelNamedVectorsFixture fixture)
    : DynamicDataModelConformanceTests<Guid>(fixture), IClassFixture<WeaviateDynamicDataModelNamedVectorsFixture>
{
}

public class WeaviateDynamicRecordConformanceTests_UnnamedVector(WeaviateDynamicDataModelUnnamedVectorFixture fixture)
    : DynamicDataModelConformanceTests<Guid>(fixture), IClassFixture<WeaviateDynamicDataModelUnnamedVectorFixture>
{
}
