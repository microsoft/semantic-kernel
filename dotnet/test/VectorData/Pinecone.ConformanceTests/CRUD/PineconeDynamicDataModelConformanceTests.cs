// Copyright (c) Microsoft. All rights reserved.

using Pinecone.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace Pinecone.ConformanceTests.CRUD;

public class PineconeDynamicDataModelConformanceTests(PineconeDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<string>(fixture), IClassFixture<PineconeDynamicDataModelFixture>
{
}
