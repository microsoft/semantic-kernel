// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone.Xunit;
using SemanticKernel.IntegrationTests.Connectors.Memory.Xunit;
using Xunit;
using Sdk = Pinecone;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone;

[Collection("PineconeVectorStoreTests")]
[PineconeApiKeySetCondition]
public class PineconeVectorStoreTests(PineconeVectorStoreFixture fixture)
    : BaseVectorStoreTests<string, PineconeHotel>(new PineconeVectorStore(fixture.Client)), IClassFixture<PineconeVectorStoreFixture>
{
    private PineconeVectorStoreFixture Fixture { get; } = fixture;

#pragma warning disable CS0618 // IPineconeVectorStoreRecordCollectionFactory is obsolete
    [VectorStoreFact]
    public void CreateCollectionUsingFactory()
    {
        var vectorStore = new PineconeVectorStore(
            this.Fixture.Client,
            new PineconeVectorStoreOptions
            {
                VectorStoreCollectionFactory = new MyVectorStoreRecordCollectionFactory()
            });

        var factoryCollection = vectorStore.GetCollection<string, PineconeHotel>(this.Fixture.IndexName);

        Assert.NotNull(factoryCollection);
        Assert.Equal("factory" + this.Fixture.IndexName, factoryCollection.CollectionName);
    }

    private sealed class MyVectorStoreRecordCollectionFactory : IPineconeVectorStoreRecordCollectionFactory
    {
        public IVectorStoreRecordCollection<TKey, TRecord> CreateVectorStoreRecordCollection<TKey, TRecord>(
            Sdk.PineconeClient pineconeClient,
            string name,
            VectorStoreRecordDefinition? vectorStoreRecordDefinition)
            where TKey : notnull
        {
            if (typeof(TKey) != typeof(string))
            {
                throw new InvalidOperationException("Only string keys are supported.");
            }

            return (new PineconeVectorStoreRecordCollection<TRecord>(pineconeClient, "factory" + name) as IVectorStoreRecordCollection<TKey, TRecord>)!;
        }
    }
#pragma warning restore CS0618
}
