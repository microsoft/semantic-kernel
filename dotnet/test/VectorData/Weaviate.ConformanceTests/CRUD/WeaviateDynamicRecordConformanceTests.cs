// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests.CRUD;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests.CRUD;

public class WeaviateDynamicRecordConformanceTests_NamedVectors(WeaviateDynamicDataModelNamedVectorsFixture fixture)
    : DynamicDataModelConformanceTests<Guid>(fixture), IClassFixture<WeaviateDynamicDataModelNamedVectorsFixture>
{
}

public class WeaviateDynamicRecordConformanceTests_UnnamedVector(WeaviateDynamicDataModelUnnamedVectorFixture fixture)
    : DynamicDataModelConformanceTests<Guid>(fixture), IClassFixture<WeaviateDynamicDataModelUnnamedVectorFixture>
{
}
