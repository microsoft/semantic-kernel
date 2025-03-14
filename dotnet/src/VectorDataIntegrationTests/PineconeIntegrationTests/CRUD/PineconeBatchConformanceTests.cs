// Copyright (c) Microsoft. All rights reserved.

using PineconeIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PineconeIntegrationTests.CRUD;

public class PineconeBatchConformanceTests(PineconeSimpleModelFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<PineconeSimpleModelFixture>
{
}
