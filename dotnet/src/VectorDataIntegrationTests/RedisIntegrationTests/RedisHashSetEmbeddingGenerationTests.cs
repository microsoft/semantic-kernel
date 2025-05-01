// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Redis;
using RedisIntegrationTests.Support;
using VectorDataSpecificationTests;
using VectorDataSpecificationTests.Support;
using Xunit;

namespace RedisIntegrationTests;

public class RedisHashSetEmbeddingGenerationTests(RedisHashSetEmbeddingGenerationTests.Fixture fixture)
    : EmbeddingGenerationTests<string>(fixture), IClassFixture<RedisHashSetEmbeddingGenerationTests.Fixture>
{
    public new class Fixture : EmbeddingGenerationTests<string>.Fixture
    {
        public override TestStore TestStore => RedisTestStore.HashSetInstance;

        public override IVectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => RedisTestStore.HashSetInstance.GetVectorStore(new() { StorageType = RedisStorageType.HashSet, EmbeddingGenerator = embeddingGenerator });

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            // TODO: This doesn't work because if a RedisVectorStoreOptions is provided (and it needs to be for HashSet), the embedding generator
            // isn't looked up in DI. The options are also immutable so we can't inject an embedding generator into them.
            // services => services
            //     .AddSingleton(RedisTestStore.HashSetInstance.Database)
            //     .AddRedisVectorStore(new RedisVectorStoreOptions() { StorageType = RedisStorageType.HashSet})
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(RedisTestStore.HashSetInstance.Database)
                .AddRedisHashSetVectorStoreRecordCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }
}
