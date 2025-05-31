// Copyright (c) Microsoft. All rights reserved.

using PineconeIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PineconeIntegrationTests.CRUD;

public class PineconeDynamicDataModelConformanceTests(PineconeDynamicDataModelFixture fixture)
    : DynamicDataModelConformanceTests<string>(fixture), IClassFixture<PineconeDynamicDataModelFixture>
{
}
