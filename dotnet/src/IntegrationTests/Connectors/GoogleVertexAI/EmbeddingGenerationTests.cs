// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Microsoft.SemanticKernel.Embeddings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.GoogleVertexAI;

public sealed class EmbeddingGenerationTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .Build();

    [Fact(Skip = "This test is for manual verification.")]
    public async Task GoogleAIEmbeddingGenerationAsync()
    {
        // Arrange
        const string Input = "LLM is Large Language Model.";
        var geminiService = new GoogleAITextEmbeddingGenerationService(this.GoogleAIGetModel(), this.GoogleAIGetApiKey());

        // Act
        var response = await geminiService.GenerateEmbeddingAsync(Input);

        // Assert
        Assert.Equal(768, response.Length);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task VertexAIEmbeddingGenerationAsync()
    {
        // Arrange
        const string Input = "LLM is Large Language Model.";
        var geminiService = new VertexAITextEmbeddingGenerationService(
            model: this.VertexAIGetModel(),
            apiKey: this.VertexAIGetApiKey(),
            location: this.VertexAIGetLocation(),
            projectId: this.VertexAIGetProjectId());

        // Act
        var response = await geminiService.GenerateEmbeddingAsync(Input);

        // Assert
        Assert.Equal(768, response.Length);
    }

    private string GoogleAIGetModel() => this._configuration.GetSection("GoogleAI:EmbeddingModelId").Get<string>()!;
    private string GoogleAIGetApiKey() => this._configuration.GetSection("GoogleAI:ApiKey").Get<string>()!;

    private string VertexAIGetModel() => this._configuration.GetSection("VertexAI:EmbeddingModelId").Get<string>()!;
    private string VertexAIGetApiKey() => this._configuration.GetSection("VertexAI:ApiKey").Get<string>()!;
    private string VertexAIGetLocation() => this._configuration.GetSection("VertexAI:Location").Get<string>()!;
    private string VertexAIGetProjectId() => this._configuration.GetSection("VertexAI:ProjectId").Get<string>()!;
}
