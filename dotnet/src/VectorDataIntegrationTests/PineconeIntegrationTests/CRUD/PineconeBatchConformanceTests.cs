// Copyright (c) Microsoft. All rights reserved.

using PineconeIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PineconeIntegrationTests.CRUD;

public class PineconeBatchConformanceTests(PineconeFixture fixture)
    : BatchConformanceTests<string>(fixture), IClassFixture<PineconeFixture>
{
}
