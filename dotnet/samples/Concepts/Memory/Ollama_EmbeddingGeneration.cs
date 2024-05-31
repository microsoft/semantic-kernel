// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Embeddings;

namespace Examples;

public class Ollama_EmbeddingGeneration : BaseTest
{
    [Fact]
    public Task RunAsync()
    {
        this.WriteLine("============= Ollama Text Embedding Generation =============");

        string modelId = TestConfiguration.Ollama.ModelId;
        Uri? baseUri = TestConfiguration.Ollama.BaseUri;

        if (modelId is null || baseUri is null)
        {
            this.WriteLine("Ollama configuration not found. Skipping example.");
            return Task.CompletedTask;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddOllamaTextEmbeddingGeneration(modelId, baseUri)
            .Build();

        return RunSampleAsync(kernel);
    }

    private async Task RunSampleAsync(Kernel kernel)
    {
        this.WriteLine("======== Text Embedding From Prompt ========");

        const string Prompt = "Describe what is GIT and why it is useful. Use simple words. Description should be long.";

        var textEmbeddingService = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        var embeddings = await textEmbeddingService.GenerateEmbeddingsAsync(new List<string> { Prompt });

        this.WriteLine(string.Join(", ", embeddings[0].ToArray()));
    }

    public Ollama_EmbeddingGeneration(ITestOutputHelper output) : base(output)
    {
    }
}
