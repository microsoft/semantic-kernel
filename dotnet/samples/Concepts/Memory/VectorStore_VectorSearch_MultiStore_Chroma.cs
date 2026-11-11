// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Azure.Identity;
using ChromaDB.Client;
using CommunityToolkit.VectorData.Chroma;
using Memory.VectorStoreFixtures;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;

namespace Memory;

/// <summary>
/// An example showing how to use common code, that can work with any vector database, with a Chroma database.
/// The common code is in the <see cref="VectorStore_VectorSearch_MultiStore_Common"/> class.
/// The common code ingests data into the vector store and then searches over that data.
/// This example is part of a set of examples each showing a different vector database.
///
/// For other databases, see the following classes:
/// <para><see cref="VectorStore_VectorSearch_MultiStore_AzureAISearch"/></para>
/// <para><see cref="VectorStore_VectorSearch_MultiStore_Qdrant"/></para>
/// <para><see cref="VectorStore_VectorSearch_MultiStore_Redis"/></para>
/// <para><see cref="VectorStore_VectorSearch_MultiStore_InMemory"/></para>
/// <para><see cref="VectorStore_VectorSearch_MultiStore_Postgres"/></para>
///
/// To run this sample, you need a local instance of Docker running, since the associated fixture will try and start a Chroma container in the local docker instance.
/// </summary>
public class VectorStore_VectorSearch_MultiStore_Chroma(ITestOutputHelper output, VectorStoreChromaContainerFixture chromaFixture) : BaseTest(output), IClassFixture<VectorStoreChromaContainerFixture>
{
    [Fact]
    public async Task ExampleWithDIAsync()
    {
        // Use the kernel for DI purposes.
        var kernelBuilder = Kernel
            .CreateBuilder();

        // Register an embedding generation service with the DI container.
        kernelBuilder.AddAzureOpenAIEmbeddingGenerator(
            deploymentName: TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
            endpoint: TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
            credential: new AzureCliCredential(),
            dimensions: 1536);

        // Initialize the Chroma docker container via the fixtures and register the Chroma VectorStore.
        await chromaFixture.ManualInitializeAsync();
        kernelBuilder.Services.AddChromaVectorStore("http://localhost:8000");

        // Register the test output helper common processor with the DI container.
        kernelBuilder.Services.AddSingleton<ITestOutputHelper>(this.Output);
        kernelBuilder.Services.AddTransient<VectorStore_VectorSearch_MultiStore_Common>();

        // Build the kernel.
        var kernel = kernelBuilder.Build();

        // Build a common processor object using the DI container.
        var processor = kernel.GetRequiredService<VectorStore_VectorSearch_MultiStore_Common>();

        // Run the process and pass a key generator function to it, to generate unique record keys.
        // The key generator function is required, since different vector stores may require different key types.
        // E.g. Chroma supports Guid and string keys, but others may not support Guid.
        await processor.IngestDataAndSearchAsync("skglossaryWithDI", () => Guid.NewGuid());
    }

    [Fact]
    public async Task ExampleWithoutDIAsync()
    {
        // Create an embedding generation service.
        var embeddingGenerator = new AzureOpenAIClient(new Uri(TestConfiguration.AzureOpenAIEmbeddings.Endpoint), new AzureCliCredential())
            .GetEmbeddingClient(TestConfiguration.AzureOpenAIEmbeddings.DeploymentName)
            .AsIEmbeddingGenerator(1536);

        // Initialize the Chroma docker container via the fixtures and construct the Chroma VectorStore.
        await chromaFixture.ManualInitializeAsync();
        var chromaClient = new ChromaClient("http://localhost:8000");
        var vectorStore = new ChromaVectorStore(chromaClient, ownsClient: true);

        // Create the common processor that works for any vector store.
        var processor = new VectorStore_VectorSearch_MultiStore_Common(vectorStore, embeddingGenerator, this.Output);

        // Run the process and pass a key generator function to it, to generate unique record keys.
        // The key generator function is required, since different vector stores may require different key types.
        // E.g. Chroma supports Guid and string keys, but others may not support Guid.
        await processor.IngestDataAndSearchAsync("skglossaryWithoutDI", () => Guid.NewGuid());
    }
}
