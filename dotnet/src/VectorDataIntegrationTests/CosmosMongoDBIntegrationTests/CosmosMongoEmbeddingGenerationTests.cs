// Copyright (c) Microsoft. All rights reserved.

using CosmosMongoDBIntegrationTests.Support;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace CosmosMongoDBIntegrationTests;

public class CosmosMongoEmbeddingGenerationTests(CosmosMongoEmbeddingGenerationTests.Fixture fixture)
    : EmbeddingGenerationTests<string>(fixture), IClassFixture<CosmosMongoEmbeddingGenerationTests.Fixture>
{
    public new class Fixture : EmbeddingGenerationTests<string>.Fixture
    {
        public override TestStore TestStore => CosmosMongoTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => CosmosMongoTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(CosmosMongoTestStore.Instance.Database)
                .AddCosmosMongoVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(CosmosMongoTestStore.Instance.Database)
                .AddCosmosMongoVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
