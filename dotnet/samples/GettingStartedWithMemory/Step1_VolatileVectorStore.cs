// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;

namespace GettingStarted;

/// <summary>
/// This example shows use a <see cref="IVectorStore"/>.
/// </summary>
public sealed class Step1_VolatileVectorStore(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// Show how to create an <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and use it to Create and Read a record.
    /// </summary>
    [Fact]
    public async Task UpsertReadDeleteRecordInVectorStoreAsync()
    {
        var kernel = Kernel
            .CreateBuilder()
            .AddVolatileVectorStore()
            .AddOpenAITextEmbeddingGeneration(
                modelId: TestConfiguration.OpenAI.EmbeddingModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey
            )
            .Build();

        var vectorStore = kernel.GetRequiredService<IVectorStore>();
        var embeddingGeneration = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        embeddingGeneration.GenerateEmbeddingAsync("Hello, world!").Wait();

        var collection = vectorStore.GetCollection<string, MyModel>("MyCollection");

        await collection.CreateCollectionIfNotExistsAsync();

        // Generate an embedding for the sample data
        var stringData = "Hello, world!";
        var embedding = await embeddingGeneration.GenerateEmbeddingAsync(stringData);

        // Upsert a record
        var recordId = await collection.UpsertAsync(new MyModel
        {
            Key = Guid.NewGuid().ToString(),
            StringData = stringData,
            Embedding = embedding,
        });
        Console.WriteLine(recordId);

        // Retrieve the record
        var retrievedData = await collection.GetAsync(recordId, new() { IncludeVectors = true });
        Console.WriteLine(retrievedData);

        // Delete the record
        await collection.DeleteAsync(recordId);

        // Try to retrieve the record again
        retrievedData = await collection.GetAsync(recordId, new() { IncludeVectors = true });
        Console.WriteLine(retrievedData);
    }

    /// <summary>
    /// Data model for the Hello World example.
    /// </summary>
    private sealed class MyModel
    {
        private readonly JsonSerializerOptions _jsonSerializerOptions = new()
        {
            WriteIndented = true,
            Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        };

        [VectorStoreRecordKey]
        public string Key { get; set; }

        [VectorStoreRecordData]
        public string StringData { get; set; }

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float> Embedding { get; set; }

        public override string ToString() => JsonSerializer.Serialize(this, _jsonSerializerOptions);
    }
}
