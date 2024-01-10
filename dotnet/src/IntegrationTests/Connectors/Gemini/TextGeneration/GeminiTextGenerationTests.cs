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
    public async Task GeminiTextGenerationAsync()
    {
        // Arrange
        const string Input = "Expand this abbreviation: LLM";

        var geminiService = new GoogleAIGeminiTextGenerationService(this.GetModel(), this.GetApiKey());

        // Act
        var response = await geminiService.GetTextContentAsync(Input);

        // Assert
        Assert.NotNull(response.Text);
        Assert.Contains("Large Language Model", response.Text, StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task GeminiTextStreamingAsync()
    {
        // Arrange
        const string Input = "Write a story about a magic backpack.";

        var geminiService = new GoogleAIGeminiTextGenerationService(this.GetModel(), this.GetApiKey());

        // Act
        var response = await geminiService.GetStreamingTextContentsAsync(Input).ToListAsync();

        // Assert
        Assert.NotEmpty(response);
        Assert.True(response.Count > 1);
        Assert.DoesNotContain(response, content => string.IsNullOrEmpty(content.Text));
    }

    private string GetModel() => this._configuration.GetSection("Gemini:ModelId").Get<string>()!;
    private string GetApiKey() => this._configuration.GetSection("Gemini:ApiKey").Get<string>()!;
}
