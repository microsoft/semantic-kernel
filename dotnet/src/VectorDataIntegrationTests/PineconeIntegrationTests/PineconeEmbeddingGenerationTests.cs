// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.SemanticKernel;
using PineconeIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace PineconeIntegrationTests;

public class PineconeEmbeddingGenerationTests(PineconeEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, PineconeEmbeddingGenerationTests.RomOfFloatVectorFixture romOfFloatVectorFixture)
    : EmbeddingGenerationTests<string>(stringVectorFixture, romOfFloatVectorFixture), IClassFixture<PineconeEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<PineconeEmbeddingGenerationTests.RomOfFloatVectorFixture>
{
    // Overriding since Pinecone requires collection names to only contain ASCII lowercase letters, digits and dashes.
    public override async Task SearchAsync_without_generator_throws()
    {
        // The database doesn't support embedding generation, and no client-side generator has been configured at any level,
        // so SearchAsync should throw.
        var collection = stringVectorFixture.GetCollection<RawRecord>(stringVectorFixture.TestStore.DefaultVectorStore, stringVectorFixture.CollectionName + "-without-generator");

        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => collection.SearchAsync("foo", top: 1).ToListAsync().AsTask());

        Assert.Equal(VectorDataStrings.NoEmbeddingGeneratorWasConfiguredForSearch, exception.Message);
    }

    public new class StringVectorFixture : EmbeddingGenerationTests<string>.StringVectorFixture
    {
        public override TestStore TestStore => PineconeTestStore.Instance;

        // https://docs.pinecone.io/troubleshooting/restrictions-on-index-names
        public override string CollectionName => "embedding-generation-tests";

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => PineconeTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(PineconeTestStore.Instance.Client)
                .AddPineconeVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(PineconeTestStore.Instance.Client)
                .AddPineconeVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class RomOfFloatVectorFixture : EmbeddingGenerationTests<string>.RomOfFloatVectorFixture
    {
        public override TestStore TestStore => PineconeTestStore.Instance;

        // https://docs.pinecone.io/troubleshooting/restrictions-on-index-names
        public override string CollectionName => "search-only-embedding-generation-tests";

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => PineconeTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(PineconeTestStore.Instance.Client)
                .AddPineconeVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(PineconeTestStore.Instance.Client)
                .AddPineconeVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
