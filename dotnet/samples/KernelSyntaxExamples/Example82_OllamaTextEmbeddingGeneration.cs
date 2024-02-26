// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example82_OllamaTextEmbeddingGeneration : BaseTest
{
    [Fact]
    public Task RunAsync()
    {
        this.WriteLine("============= Ollama Text Embedding Generation =============");

        // string modelId = TestConfiguration.Ollama.ModelId;
        // Uri? baseUri = TestConfiguration.Ollama.BaseUri;

        string modelId = "llama2:7b-chat-q4_K_M";
        Uri? baseUri = new Uri("http://100.77.129.101:11434");

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

        const string prompt = "Describe what is GIT and why it is useful. Use simple words. Description should be long.";

        var textEmbeddingService = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        var embeddings = await textEmbeddingService.GenerateEmbeddingsAsync(new List<string> { prompt });

        this.WriteLine(embeddings[0]);
    }

    public Example82_OllamaTextEmbeddingGeneration(ITestOutputHelper output) : base(output)
    {
    }
}
