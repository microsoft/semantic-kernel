// Copyright (c) Microsoft. All rights reserved.

using PineconeIntegrationTests.Support;
using VectorDataSpecificationTests.CRUD;
using Xunit;

namespace PineconeIntegrationTests.CRUD;

public class PineconeRecordConformanceTests(PineconeSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<PineconeSimpleModelFixture>
{
}
