// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Memory.VectorStoreFixtures;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Connectors.Redis;
using StackExchange.Redis;

namespace Memory;

/// <summary>
/// An example showing how to use common code, that can work with any vector database, with a Redis database.
/// The common code is in the <see cref="VectorStore_VectorSearch_MultiStore_Common"/> class.
/// The common code ingests data into the vector store and then searches over that data.
/// This example is part of a set of examples each showing a different vector database.
///
/// For other databases, see the following classes:
/// <para><see cref="VectorStore_VectorSearch_MultiStore_AzureAISearch"/></para>
/// <para><see cref="VectorStore_VectorSearch_MultiStore_Qdrant"/></para>
/// <para><see cref="VectorStore_VectorSearch_MultiStore_InMemory"/></para>
/// <para><see cref="VectorStore_VectorSearch_MultiStore_Postgres"/></para>
///
/// Redis supports two record storage types: Json and HashSet.
/// Note the use of the <see cref="RedisStorageType"/> enum to specify the preferred storage type.
///
/// To run this sample, you need a local instance of Docker running, since the associated fixture will try and start a Redis container in the local docker instance.
/// </summary>
public class VectorStore_VectorSearch_MultiStore_Redis(ITestOutputHelper output, VectorStoreRedisContainerFixture redisFixture) : BaseTest(output), IClassFixture<VectorStoreRedisContainerFixture>
{
    [Theory]
    [InlineData(RedisStorageType.Json)]
    [InlineData(RedisStorageType.HashSet)]
    public async Task ExampleWithDIAsync(RedisStorageType redisStorageType)
    {
        // Use the kernel for DI purposes.
        var kernelBuilder = Kernel
            .CreateBuilder();

        // Register an embedding generation service with the DI container.
        kernelBuilder.AddAzureOpenAITextEmbeddingGeneration(
            deploymentName: TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
            endpoint: TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
            credential: new AzureCliCredential());

        // Initialize the Redis docker container via the fixtures and register the Redis VectorStore with the preferred storage type.
        await redisFixture.ManualInitializeAsync();
        kernelBuilder.AddRedisVectorStore("localhost:6379", new() { StorageType = redisStorageType });

        // Register the test output helper common processor with the DI container.
        kernelBuilder.Services.AddSingleton<ITestOutputHelper>(this.Output);
        kernelBuilder.Services.AddTransient<VectorStore_VectorSearch_MultiStore_Common>();

        // Build the kernel.
        var kernel = kernelBuilder.Build();

        // Build a common processor object using the DI container.
        var processor = kernel.GetRequiredService<VectorStore_VectorSearch_MultiStore_Common>();

        // Run the process and pass a key generator function to it, to generate unique record keys.
        // The key generator function is required, since different vector stores may require different key types.
        // E.g. Redis supports string keys, but others may not support string.
        // Also note that we are appending the collection name with the storage type so that we have two separate collections,
        // since a redis index for JSON records cannot be used to index hashset documents, and vice versa.
        await processor.IngestDataAndSearchAsync("skglossaryWithDI" + redisStorageType, () => Guid.NewGuid().ToString());
    }

    [Theory]
    [InlineData(RedisStorageType.Json)]
    [InlineData(RedisStorageType.HashSet)]
    public async Task ExampleWithoutDIAsync(RedisStorageType redisStorageType)
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());

        // Initialize the Redis docker container via the fixtures and construct the Redis VectorStore with the preferred storage type.
        await redisFixture.ManualInitializeAsync();
        var database = ConnectionMultiplexer.Connect("localhost:6379").GetDatabase();
        var vectorStore = new RedisVectorStore(database, new() { StorageType = redisStorageType });

        // Create the common processor that works for any vector store.
        var processor = new VectorStore_VectorSearch_MultiStore_Common(vectorStore, textEmbeddingGenerationService, this.Output);

        // Run the process and pass a key generator function to it, to generate unique record keys.
        // The key generator function is required, since different vector stores may require different key types.
        // E.g. Redis supports string keys, but others may not support string.
        // Also note that we are appending the collection name with the storage type so that we have two separate collections,
        // since a redis index for JSON records cannot be used to index hashset documents, and vice versa.
        await processor.IngestDataAndSearchAsync("skglossaryWithoutDI" + redisStorageType, () => Guid.NewGuid().ToString());
    }
}
