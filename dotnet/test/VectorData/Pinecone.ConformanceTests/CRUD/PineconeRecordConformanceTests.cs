// Copyright (c) Microsoft. All rights reserved.

using Pinecone.ConformanceTests.Support;
using VectorData.ConformanceTests.CRUD;
using Xunit;

namespace Pinecone.ConformanceTests.CRUD;

public class PineconeRecordConformanceTests(PineconeSimpleModelFixture fixture)
    : RecordConformanceTests<string>(fixture), IClassFixture<PineconeSimpleModelFixture>
{
}
