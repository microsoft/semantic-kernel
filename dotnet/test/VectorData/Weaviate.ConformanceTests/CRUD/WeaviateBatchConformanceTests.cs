// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.CRUD;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.CRUD;

public class WeaviateBatchConformanceTests_NamedVectors(WeaviateSimpleModelNamedVectorsFixture fixture)
    : BatchConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelNamedVectorsFixture>
{
}

public class WeaviateBatchConformanceTests_UnnamedVector(WeaviateSimpleModelUnnamedVectorFixture fixture)
    : BatchConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelUnnamedVectorFixture>
{
}
