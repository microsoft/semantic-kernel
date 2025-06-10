// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.CRUD;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.CRUD;

public class WeaviateRecordConformanceTests_NamedVectors(WeaviateSimpleModelNamedVectorsFixture fixture)
    : RecordConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelNamedVectorsFixture>
{
}

public class WeaviateRecordConformanceTests_UnnamedVector(WeaviateSimpleModelUnnamedVectorFixture fixture)
    : RecordConformanceTests<Guid>(fixture), IClassFixture<WeaviateSimpleModelUnnamedVectorFixture>
{
}
