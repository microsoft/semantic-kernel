// Copyright (c) Microsoft. All rights reserved.

using AzureAISearchIntegrationTests.Support;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using VectorDataSpecificationTests.Xunit;
using Xunit;

namespace AzureAISearchIntegrationTests;

public class AzureAISearchEmbeddingGenerationTests(AzureAISearchEmbeddingGenerationTests.Fixture fixture)
    : EmbeddingGenerationTests<string>(fixture), IClassFixture<AzureAISearchEmbeddingGenerationTests.Fixture>
{
    [ConditionalFact(Skip = "SearchAsync without a generator delegates to the service for AzureAISearch")]
    public override Task SearchAsync_without_generator_throws()
    {
        return base.SearchAsync_without_generator_throws();
    }

    public new class Fixture : EmbeddingGenerationTests<string>.Fixture
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
                .AddAzureAISearchVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
