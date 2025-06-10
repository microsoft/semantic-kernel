// Copyright (c) Microsoft. All rights reserved.

using AzureAISearch.ConformanceTests.Support;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace AzureAISearch.ConformanceTests;

public class AzureAISearchEmbeddingGenerationTests(AzureAISearchEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, AzureAISearchEmbeddingGenerationTests.RomOfFloatVectorFixture romOfFloatVectorFixture)
    : EmbeddingGenerationTests<string>(stringVectorFixture, romOfFloatVectorFixture), IClassFixture<AzureAISearchEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<AzureAISearchEmbeddingGenerationTests.RomOfFloatVectorFixture>
{
    // SearchAsync without a generator delegates to the service for AzureAISearch
    public override Task SearchAsync_string_without_generator_throws()
        => Task.CompletedTask;

    public new class StringVectorFixture : EmbeddingGenerationTests<string>.StringVectorFixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;

        // Azure AI search only supports lowercase letters, digits or dashes.
        public override string CollectionName => "embedding-gen-tests" + AzureAISearchTestEnvironment.TestIndexPostfix;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => AzureAISearchTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(AzureAISearchTestStore.Instance.Client)
                .AddAzureAISearchVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(AzureAISearchTestStore.Instance.Client)
                .AddAzureAISearchCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class RomOfFloatVectorFixture : EmbeddingGenerationTests<string>.RomOfFloatVectorFixture
    {
        public override TestStore TestStore => AzureAISearchTestStore.Instance;

        // Azure AI search only supports lowercase letters, digits or dashes.
        public override string CollectionName => "search-only-embedding-gen-tests" + AzureAISearchTestEnvironment.TestIndexPostfix;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => AzureAISearchTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(AzureAISearchTestStore.Instance.Client)
                .AddAzureAISearchVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(AzureAISearchTestStore.Instance.Client)
                .AddAzureAISearchCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
