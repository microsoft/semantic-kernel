// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using CosmosNoSql.ConformanceTests.Support;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.CosmosNoSql;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace CosmosNoSql.ConformanceTests;

#pragma warning disable CA2000 // Dispose objects before losing scope

public class CosmosNoSqlEmbeddingGenerationTests(CosmosNoSqlEmbeddingGenerationTests.StringVectorFixture stringVectorFixture, CosmosNoSqlEmbeddingGenerationTests.RomOfFloatVectorFixture romOfFloatVectorFixture)
    : EmbeddingGenerationTests<string>(stringVectorFixture, romOfFloatVectorFixture), IClassFixture<CosmosNoSqlEmbeddingGenerationTests.StringVectorFixture>, IClassFixture<CosmosNoSqlEmbeddingGenerationTests.RomOfFloatVectorFixture>
{
    // Override the DI tests because the base tests call vectorStore.GetCollection<string, Record>()
    // but CosmosNoSqlVectorStore.GetCollection requires CosmosNoSqlKey, not plain string.
    public override async Task SearchAsync_with_store_dependency_injection()
    {
        foreach (var registrationDelegate in stringVectorFixture.DependencyInjectionStoreRegistrationDelegates)
        {
            IServiceCollection serviceCollection = new ServiceCollection();

            serviceCollection.AddSingleton<IEmbeddingGenerator>(new FakeEmbeddingGenerator(replaceLast: 1));
            registrationDelegate(serviceCollection);

            await using var serviceProvider = serviceCollection.BuildServiceProvider();

            var vectorStore = serviceProvider.GetRequiredService<VectorStore>();
            // Use the fixture's GetCollection override which routes through TestStore adapter
            var collection = stringVectorFixture.GetCollection<Record>(vectorStore, stringVectorFixture.CollectionName, stringVectorFixture.CreateRecordDefinition());

            var result = await collection.SearchAsync("[1, 1, 0]", top: 1).SingleAsync();

            Assert.Equal("Store ([1, 1, 1])", result.Record.Text);
        }
    }

    public override async Task SearchAsync_with_collection_dependency_injection()
    {
        foreach (var registrationDelegate in stringVectorFixture.DependencyInjectionCollectionRegistrationDelegates)
        {
            IServiceCollection serviceCollection = new ServiceCollection();

            serviceCollection.AddSingleton<IEmbeddingGenerator>(new FakeEmbeddingGenerator(replaceLast: 1));
            registrationDelegate(serviceCollection);

            await using var serviceProvider = serviceCollection.BuildServiceProvider();

            // Resolve with CosmosNoSqlKey since that's how AddAbstractions registers it,
            // then wrap with the adapter for plain string key usage.
            var innerCollection = serviceProvider.GetRequiredService<VectorStoreCollection<CosmosNoSqlKey, RecordWithAttributes>>();
            var collection = new CosmosNoSqlCollectionAdapter<string, RecordWithAttributes>(innerCollection);

            var result = await collection.SearchAsync("[1, 1, 0]", top: 1).SingleAsync();

            Assert.Equal("Store ([1, 1, 1])", result.Record.Text);
        }
    }
    public new class StringVectorFixture : EmbeddingGenerationTests<string>.StringVectorFixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => CosmosNoSqlTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override VectorStoreCollection<string, TRecord> GetCollection<TRecord>(
            VectorStore vectorStore,
            string collectionName,
            VectorStoreCollectionDefinition? recordDefinition = null)
        {
            // If no definition was provided, build one from TRecord's attributes.
            recordDefinition ??= BuildDefinitionFromType(typeof(TRecord));

            // If the VectorStore has a store-level embedding generator, copy it onto the definition
            // so that TestStore.CreateCollection can pass it to the collection options.
            if (recordDefinition.EmbeddingGenerator is null
                && vectorStore is CosmosNoSqlVectorStore cosmosStore)
            {
                var field = typeof(CosmosNoSqlVectorStore).GetField("_embeddingGenerator", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
                if (field?.GetValue(cosmosStore) is IEmbeddingGenerator generator)
                {
                    recordDefinition.EmbeddingGenerator = generator;
                }
            }

            return this.CreateCollection<string, TRecord>(collectionName, recordDefinition);
        }

        public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(
            VectorStore vectorStore,
            string collectionName,
            VectorStoreCollectionDefinition recordDefinition)
        {
            if (recordDefinition.EmbeddingGenerator is null
                && vectorStore is CosmosNoSqlVectorStore cosmosStore)
            {
                var field = typeof(CosmosNoSqlVectorStore).GetField("_embeddingGenerator", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
                if (field?.GetValue(cosmosStore) is IEmbeddingGenerator generator)
                {
                    recordDefinition.EmbeddingGenerator = generator;
                }
            }

            return this.CreateDynamicCollection(collectionName, recordDefinition);
        }

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(CosmosNoSqlTestStore.Instance.Database)
                .AddCosmosNoSqlVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(CosmosNoSqlTestStore.Instance.Database)
                .AddCosmosNoSqlCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }

    public new class RomOfFloatVectorFixture : EmbeddingGenerationTests<string>.RomOfFloatVectorFixture
    {
        public override TestStore TestStore => CosmosNoSqlTestStore.Instance;

        public override VectorStore CreateVectorStore(IEmbeddingGenerator? embeddingGenerator)
            => CosmosNoSqlTestStore.Instance.GetVectorStore(new() { EmbeddingGenerator = embeddingGenerator });

        public override VectorStoreCollection<string, TRecord> GetCollection<TRecord>(
            VectorStore vectorStore,
            string collectionName,
            VectorStoreCollectionDefinition? recordDefinition = null)
        {
            // If no definition was provided, build one from TRecord's attributes.
            recordDefinition ??= BuildDefinitionFromType(typeof(TRecord));

            // If the VectorStore has a store-level embedding generator, copy it onto the definition
            // so that TestStore.CreateCollection can pass it to the collection options.
            if (recordDefinition.EmbeddingGenerator is null
                && vectorStore is CosmosNoSqlVectorStore cosmosStore)
            {
                var field = typeof(CosmosNoSqlVectorStore).GetField("_embeddingGenerator", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
                if (field?.GetValue(cosmosStore) is IEmbeddingGenerator generator)
                {
                    recordDefinition.EmbeddingGenerator = generator;
                }
            }

            return this.CreateCollection<string, TRecord>(collectionName, recordDefinition);
        }

        public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(
            VectorStore vectorStore,
            string collectionName,
            VectorStoreCollectionDefinition recordDefinition)
        {
            if (recordDefinition.EmbeddingGenerator is null
                && vectorStore is CosmosNoSqlVectorStore cosmosStore)
            {
                var field = typeof(CosmosNoSqlVectorStore).GetField("_embeddingGenerator", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
                if (field?.GetValue(cosmosStore) is IEmbeddingGenerator generator)
                {
                    recordDefinition.EmbeddingGenerator = generator;
                }
            }

            return this.CreateDynamicCollection(collectionName, recordDefinition);
        }

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionStoreRegistrationDelegates =>
        [
            services => services
                .AddSingleton(CosmosNoSqlTestStore.Instance.Database)
                .AddCosmosNoSqlVectorStore()
        ];

        public override Func<IServiceCollection, IServiceCollection>[] DependencyInjectionCollectionRegistrationDelegates =>
        [
            services => services
                .AddSingleton(CosmosNoSqlTestStore.Instance.Database)
                .AddCosmosNoSqlCollection<RecordWithAttributes>(this.CollectionName)
        ];
    }

    /// <summary>
    /// Builds a VectorStoreCollectionDefinition from a record type's VectorStore attributes.
    /// Used when GetCollection is called without an explicit definition.
    /// </summary>
    private static VectorStoreCollectionDefinition BuildDefinitionFromType(Type recordType)
    {
        var properties = new List<VectorStoreProperty>();
        foreach (var prop in recordType.GetProperties())
        {
            if (prop.GetCustomAttribute<VectorStoreKeyAttribute>() is not null)
            {
                properties.Add(new VectorStoreKeyProperty(prop.Name, prop.PropertyType));
            }
            else if (prop.GetCustomAttribute<VectorStoreVectorAttribute>() is VectorStoreVectorAttribute vecAttr)
            {
                properties.Add(new VectorStoreVectorProperty(prop.Name, prop.PropertyType, vecAttr.Dimensions));
            }
            else if (prop.GetCustomAttribute<VectorStoreDataAttribute>() is not null)
            {
                properties.Add(new VectorStoreDataProperty(prop.Name, prop.PropertyType));
            }
        }

        return new VectorStoreCollectionDefinition { Properties = properties };
    }
}
