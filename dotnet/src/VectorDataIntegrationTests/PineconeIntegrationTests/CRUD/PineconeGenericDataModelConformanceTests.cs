// Copyright (c) Microsoft. All rights reserved.

using PineconeIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PineconeIntegrationTests.CRUD;

public class PineconeGenericDataModelConformanceTests(PineconeGenericDataModelFixture fixture)
    : GenericDataModelConformanceTests<string>(fixture), IClassFixture<PineconeGenericDataModelFixture>
{
}
