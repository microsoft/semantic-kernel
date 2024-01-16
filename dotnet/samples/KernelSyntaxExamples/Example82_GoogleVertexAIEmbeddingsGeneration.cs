// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public sealed class Example82_GoogleVertexAIEmbeddingsGeneration : BaseTest
{
    [Fact]
    public async Task RunAsync()
    {
        this.WriteLine("======== Gemini Chat Completion ========");

        await GoogleAIGeminiAsync();
        await VertexAIGeminiAsync();
    }

    private async Task GoogleAIGeminiAsync()
    {
        this.WriteLine("===== Google AI Gemini API =====");

        string geminiApiKey = TestConfiguration.GoogleAI.Gemini.ApiKey;
        string geminiModelId = TestConfiguration.GoogleAI.Gemini.ModelId;

        if (geminiApiKey is null || geminiModelId is null)
        {
            this.WriteLine("Gemini credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddGoogleAIEmbeddingsGeneration(
                modelId: geminiModelId,
                apiKey: geminiApiKey)
            .Build();

        await RunSampleAsync(kernel);
    }

    private async Task VertexAIGeminiAsync()
    {
        this.WriteLine("===== Vertex AI Gemini API =====");

        string geminiApiKey = TestConfiguration.VertexAI.Gemini.ApiKey;
        string geminiModelId = TestConfiguration.VertexAI.Gemini.ModelId;
        string geminiLocation = TestConfiguration.VertexAI.Gemini.Location;
        string geminiProject = TestConfiguration.VertexAI.Gemini.ProjectId;

        if (geminiApiKey is null || geminiModelId is null || geminiLocation is null || geminiProject is null)
        {
            this.WriteLine("Gemini vertex ai credentials not found. Skipping example.");
            return;
        }

        Kernel kernel = Kernel.CreateBuilder()
            .AddVertexAIEmbeddingsGeneration(
                modelId: geminiModelId,
                apiKey: geminiApiKey,
                location: geminiLocation,
                projectId: geminiProject)
            .Build();

        await RunSampleAsync(kernel);
    }

    private async Task RunSampleAsync(Kernel kernel)
    {
        var embeddingGenerator = kernel.GetRequiredService<ITextEmbeddingGenerationService>();
        ReadOnlyMemory<float> embeddings = await embeddingGenerator.GenerateEmbeddingAsync("Hello world!");
        this.WriteLine("Embeddings:");
        for (int i = 0; i < embeddings.Span.Length; i++)
        {
            float embedding = embeddings.Span[i];
            this.WriteLine($"{embedding}");
        }
    }

    public Example82_GoogleVertexAIEmbeddingsGeneration(ITestOutputHelper output) : base(output) { }
}
