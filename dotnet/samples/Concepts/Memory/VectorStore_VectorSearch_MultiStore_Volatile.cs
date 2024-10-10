// Copyright (c) Microsoft. All rights reserved.

using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Data;

namespace Memory;

/// <summary>
/// An example showing how to use common code, that can work with any vector database, with the Volatile (in-memory) vector store.
/// The common code is in the <see cref="VectorStore_VectorSearch_MultiStore_Common"/> class.
/// The common code ingests data into the vector store and then searches over that data.
/// This example is part of a set of examples each showing a different vector database.
///
/// For other databases, see the following classes:
/// <para><see cref="VectorStore_VectorSearch_MultiStore_AzureAISearch"/></para>
/// <para><see cref="VectorStore_VectorSearch_MultiStore_Redis"/></para>
/// <para><see cref="VectorStore_VectorSearch_MultiStore_Qdrant"/></para>
/// </summary>
public class VectorStore_VectorSearch_MultiStore_Volatile(ITestOutputHelper output) : BaseTest(output)
{
    [Fact]
    public async Task ExampleWitDIAsync()
    {
        // Use the kernel for DI purposes.
        var kernelBuilder = Kernel
            .CreateBuilder();

        // Register an embedding generation service with the DI container.
        kernelBuilder.AddAzureOpenAITextEmbeddingGeneration(
            deploymentName: TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
            endpoint: TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
            credential: new AzureCliCredential());

        // Register the Volatile VectorStore.
        kernelBuilder.AddVolatileVectorStore();

        // Register the test output helper common processor with the DI container.
        kernelBuilder.Services.AddSingleton<ITestOutputHelper>(this.Output);
        kernelBuilder.Services.AddTransient<VectorStore_VectorSearch_MultiStore_Common>();

        // Build the kernel.
        var kernel = kernelBuilder.Build();

        // Build a common processor object using the DI container.
        var processor = kernel.GetRequiredService<VectorStore_VectorSearch_MultiStore_Common>();

        // Run the process and pass a key generator function to it, to generate unique record keys.
        // The key generator function is required, since different vector stores may require different key types.
        // E.g. Volatile supports any comparible type, but others may only support string or Guid or ulong, etc.
        // For this example we'll use int.
        var uniqueId = 0;
        await processor.IngestDataAndSearchAsync("skglossaryWithDI", () => uniqueId++);
    }

    [Fact]
    public async Task ExampleWithoutDIAsync()
    {
        // Create an embedding generation service.
        var textEmbeddingGenerationService = new AzureOpenAITextEmbeddingGenerationService(
                TestConfiguration.AzureOpenAIEmbeddings.DeploymentName,
                TestConfiguration.AzureOpenAIEmbeddings.Endpoint,
                new AzureCliCredential());

        // Construct the Volatile VectorStore.
        var vectorStore = new VolatileVectorStore();

        // Create the common processor that works for any vector store.
        var processor = new VectorStore_VectorSearch_MultiStore_Common(vectorStore, textEmbeddingGenerationService, this.Output);

        // Run the process and pass a key generator function to it, to generate unique record keys.
        // The key generator function is required, since different vector stores may require different key types.
        // E.g. Volatile supports any comparible type, but others may only support string or Guid or ulong, etc.
        // For this example we'll use int.
        var uniqueId = 0;
        await processor.IngestDataAndSearchAsync("skglossaryWithoutDI", () => uniqueId++);
    }
}
