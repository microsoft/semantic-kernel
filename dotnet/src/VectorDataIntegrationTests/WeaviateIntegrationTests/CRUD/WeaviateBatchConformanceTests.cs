// Copyright (c) Microsoft. All rights reserved.

using VectorDataSpecificationTests.CRUD;
using WeaviateIntegrationTests.Support;
using Xunit;

namespace WeaviateIntegrationTests.CRUD;

public class WeaviateBatchConformanceTests_NamedVectors(WeaviateSimpleModelNamedVectorsFixture fixture)
    : BatchConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelNamedVectorsFixture>
{
}

public class WeaviateBatchConformanceTests_UnnamedVector(WeaviateSimpleModelUnnamedVectorFixture fixture)
    : BatchConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelUnnamedVectorFixture>
{
}
