#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.Gemini;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Gemini.TextGeneration;

public sealed class GeminiTextGenerationTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .Build();

    [Fact(Skip = "This test is for manual verification.")]
    public async Task GoogleAIGeminiTextGenerationAsync()
    {
        // Arrange
        const string Input = "Expand this abbreviation: LLM";

        var geminiService = new GoogleAIGeminiTextGenerationService(this.GoogleAIGetModel(), this.GoogleAIGetApiKey());

        // Act
        var response = await geminiService.GetTextContentAsync(Input);

        // Assert
        Assert.NotNull(response.Text);
        Assert.Contains("Large Language Model", response.Text, StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task GoogleAIGeminiTextStreamingAsync()
    {
        // Arrange
        const string Input = "Write a story about a magic backpack.";

        var geminiService = new GoogleAIGeminiTextGenerationService(this.GoogleAIGetModel(), this.GoogleAIGetApiKey());

        // Act
        var response = await geminiService.GetStreamingTextContentsAsync(Input).ToListAsync();

        // Assert
        Assert.NotEmpty(response);
        Assert.True(response.Count > 1);
        Assert.DoesNotContain(response, content => string.IsNullOrEmpty(content.Text));
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task VertexAIGeminiTextGenerationAsync()
    {
        // Arrange
        const string Input = "Expand this abbreviation: LLM";

        var geminiService = new VertexAIGeminiTextGenerationService(
            model: this.VertexAIGetModel(),
            apiKey: this.VertexAIGetApiKey(),
            location: this.VertexAIGetLocation(),
            projectId: this.VertexAIGetProjectId());

        // Act
        var response = await geminiService.GetTextContentAsync(Input);

        // Assert
        Assert.NotNull(response.Text);
        Assert.Contains("Large Language Model", response.Text, StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task VertexAIGeminiTextStreamingAsync()
    {
        // Arrange
        const string Input = "Write a story about a magic backpack.";

        var geminiService = new VertexAIGeminiTextGenerationService(
            model: this.VertexAIGetModel(),
            apiKey: this.VertexAIGetApiKey(),
            location: this.VertexAIGetLocation(),
            projectId: this.VertexAIGetProjectId());

        // Act
        var response = await geminiService.GetStreamingTextContentsAsync(Input).ToListAsync();

        // Assert
        Assert.NotEmpty(response);
        Assert.True(response.Count > 1);
        Assert.DoesNotContain(response, content => string.IsNullOrEmpty(content.Text));
    }

    private string GoogleAIGetModel() => this._configuration.GetSection("GoogleAI:Gemini:ModelId").Get<string>()!;
    private string GoogleAIGetApiKey() => this._configuration.GetSection("GoogleAI:Gemini:ApiKey").Get<string>()!;

    private string VertexAIGetModel() => this._configuration.GetSection("VertexAI:Gemini:ModelId").Get<string>()!;
    private string VertexAIGetApiKey() => this._configuration.GetSection("VertexAI:Gemini:ApiKey").Get<string>()!;
    private string VertexAIGetLocation() => this._configuration.GetSection("VertexAI:Gemini:Location").Get<string>()!;
    private string VertexAIGetProjectId() => this._configuration.GetSection("VertexAI:Gemini:ProjectId").Get<string>()!;
}
