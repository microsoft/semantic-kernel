// Copyright (c) Microsoft. All rights reserved.

using Google.Apis.Auth.OAuth2;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Embeddings;
using xRetry;

namespace Memory;

// The following example shows how to use Semantic Kernel with Google AI and Google's Vertex AI for embedding generation,
// including the ability to specify custom dimensions.
public class Google_EmbeddingGeneration(ITestOutputHelper output) : BaseTest(output)
{
    /// <summary>
    /// This test demonstrates how to use the Google Vertex AI embedding generation service with default dimensions.
    /// </summary>
    /// <remarks>
    /// Currently custom dimensions are not supported for Vertex AI.
    /// </remarks>
    [RetryFact(typeof(HttpOperationException))]
    public async Task GenerateEmbeddingWithDefaultDimensionsUsingVertexAI()
    {
        string? bearerToken = null;

        Assert.NotNull(TestConfiguration.VertexAI.EmbeddingModelId);
        Assert.NotNull(TestConfiguration.VertexAI.ClientId);
        Assert.NotNull(TestConfiguration.VertexAI.ClientSecret);
        Assert.NotNull(TestConfiguration.VertexAI.Location);
        Assert.NotNull(TestConfiguration.VertexAI.ProjectId);

        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddVertexAIEmbeddingGeneration(
                modelId: TestConfiguration.VertexAI.EmbeddingModelId!,
                bearerTokenProvider: GetBearerToken,
                location: TestConfiguration.VertexAI.Location,
                projectId: TestConfiguration.VertexAI.ProjectId);
        Kernel kernel = kernelBuilder.Build();

        var embeddingGenerator = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        // Generate embeddings with the default dimensions for the model
        var embeddings = await embeddingGenerator.GenerateEmbeddingsAsync(
            ["Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your codebase."]);

        Console.WriteLine($"Generated '{embeddings.Count}' embedding(s) with '{embeddings[0].Length}' dimensions (default) for the provided text");

        // Uses Google.Apis.Auth.OAuth2 to get the bearer token
        async ValueTask<string> GetBearerToken()
        {
            if (!string.IsNullOrEmpty(bearerToken))
            {
                return bearerToken;
            }

            var credential = GoogleWebAuthorizationBroker.AuthorizeAsync(
                new ClientSecrets
                {
                    ClientId = TestConfiguration.VertexAI.ClientId,
                    ClientSecret = TestConfiguration.VertexAI.ClientSecret
                },
                ["https://www.googleapis.com/auth/cloud-platform"],
                "user",
                CancellationToken.None);

            var userCredential = await credential.WaitAsync(CancellationToken.None);
            bearerToken = userCredential.Token.AccessToken;

            return bearerToken;
        }
    }

    [RetryFact(typeof(HttpOperationException))]
    public async Task GenerateEmbeddingWithDefaultDimensionsUsingGoogleAI()
    {
        Assert.NotNull(TestConfiguration.GoogleAI.EmbeddingModelId);
        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);

        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddGoogleAIEmbeddingGeneration(
                modelId: TestConfiguration.GoogleAI.EmbeddingModelId!,
                apiKey: TestConfiguration.GoogleAI.ApiKey);
        Kernel kernel = kernelBuilder.Build();

        var embeddingGenerator = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        // Generate embeddings with the default dimensions for the model
        var embeddings = await embeddingGenerator.GenerateEmbeddingsAsync(
            ["Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your codebase."]);

        Console.WriteLine($"Generated '{embeddings.Count}' embedding(s) with '{embeddings[0].Length}' dimensions (default) for the provided text");
    }

    [RetryFact(typeof(HttpOperationException))]
    public async Task GenerateEmbeddingWithCustomDimensionsUsingGoogleAI()
    {
        Assert.NotNull(TestConfiguration.GoogleAI.EmbeddingModelId);
        Assert.NotNull(TestConfiguration.GoogleAI.ApiKey);

        // Specify custom dimensions for the embeddings
        const int CustomDimensions = 512;

        IKernelBuilder kernelBuilder = Kernel.CreateBuilder();
        kernelBuilder.AddGoogleAIEmbeddingGeneration(
                modelId: TestConfiguration.GoogleAI.EmbeddingModelId!,
                apiKey: TestConfiguration.GoogleAI.ApiKey,
                dimensions: CustomDimensions);
        Kernel kernel = kernelBuilder.Build();

        var embeddingGenerator = kernel.GetRequiredService<ITextEmbeddingGenerationService>();

        // Generate embeddings with the specified custom dimensions
        var embeddings = await embeddingGenerator.GenerateEmbeddingsAsync(
            ["Semantic Kernel is a lightweight, open-source development kit that lets you easily build AI agents and integrate the latest AI models into your codebase."]);

        Console.WriteLine($"Generated '{embeddings.Count}' embedding(s) with '{embeddings[0].Length}' dimensions (custom: '{CustomDimensions}') for the provided text");

        // Verify that we received embeddings with our requested dimensions
        Assert.Equal(CustomDimensions, embeddings[0].Length);
    }
}
