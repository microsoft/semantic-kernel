// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Microsoft.SemanticKernel.Data;
using SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone.Xunit;
using Xunit;
using Sdk = Pinecone;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone;

[Collection("PineconeVectorStoreTests")]
[PineconeApiKeySetCondition]
public class PineconeVectorStoreTests(PineconeVectorStoreFixture fixture) : IClassFixture<PineconeVectorStoreFixture>
{
    private PineconeVectorStoreFixture Fixture { get; } = fixture;

    [PineconeFact]
    public async Task ListCollectionNamesAsync()
    {
        var collectionNames = await this.Fixture.VectorStore.ListCollectionNamesAsync().ToListAsync();

        Assert.Equal([this.Fixture.IndexName], collectionNames);
    }

    [PineconeFact]
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
            where TRecord : class
        {
            if (typeof(TKey) != typeof(string))
            {
                throw new InvalidOperationException("Only string keys are supported.");
            }

            return (new PineconeVectorStoreRecordCollection<TRecord>(pineconeClient, "factory" + name) as IVectorStoreRecordCollection<TKey, TRecord>)!;
        }
    }
}
