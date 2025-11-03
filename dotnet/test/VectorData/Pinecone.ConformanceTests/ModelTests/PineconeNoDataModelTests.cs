// Copyright (c) Microsoft. All rights reserved.

using Pinecone.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Pinecone.ConformanceTests.ModelTests;

public class PineconeNoDataModelTests(PineconeNoDataModelTests.Fixture fixture)
    : NoDataModelTests<string>(fixture), IClassFixture<PineconeNoDataModelTests.Fixture>
{
    public new class Fixture : NoDataModelTests<string>.Fixture
    {
        public override TestStore TestStore => PineconeTestStore.Instance;

        // https://docs.pinecone.io/troubleshooting/restrictions-on-index-names
        public override string CollectionName => "no-data-model-tests";
    }
}
