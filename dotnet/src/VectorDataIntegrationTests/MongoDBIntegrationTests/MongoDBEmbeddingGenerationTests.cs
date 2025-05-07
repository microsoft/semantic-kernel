// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using MongoDBIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace MongoDBIntegrationTests;

public class MongoDBEmbeddingGenerationTests(MongoDBEmbeddingGenerationTests.Fixture fixture)
    : EmbeddingGenerationTests<string>(fixture), IClassFixture<MongoDBEmbeddingGenerationTests.Fixture>
{
    public new class Fixture : EmbeddingGenerationTests<string>.Fixture
    {
        public override TestStore TestStore => MongoDBTestStore.Instance;

        public override IVectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => MongoDBTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(MongoDBTestStore.Instance.Database)
                .AddMongoDBVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(MongoDBTestStore.Instance.Database)
                .AddMongoDBVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
