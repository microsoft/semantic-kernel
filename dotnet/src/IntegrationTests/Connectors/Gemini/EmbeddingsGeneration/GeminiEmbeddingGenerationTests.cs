#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.Gemini;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Gemini.EmbeddingsGeneration;

public sealed class GeminiEmbeddingGenerationTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .Build();

    [Fact(Skip = "This test is for manual verification.")]
    public async Task GeminiEmbeddingsGenerationAsync()
    {
        // Arrange
        const string Input = "Expand this abbreviation: LLM";
        var geminiService = new GoogleAIGeminiTextEmbeddingGenerationService(this.GetModel(), this.GetApiKey());

        // Act
        var response = await geminiService.GenerateEmbeddingAsync(Input);

        // Assert
        Assert.Equal(768, response.Length);
    }

    private string GetModel() => this._configuration.GetSection("Gemini:EmbeddingModelId").Get<string>()!;
    private string GetApiKey() => this._configuration.GetSection("Gemini:ApiKey").Get<string>()!;
}
