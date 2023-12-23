#region HEADER
// Copyright (c) Microsoft. All rights reserved.
#endregion

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.Gemini;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Gemini.TextGeneration;

public class GeminiTextGenerationTests
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .Build();

    // Load configuration
    [Fact(Skip = "This test is for manual verification.")]
    public async Task GeminiTextGenerationAsync()
    {
        // Arrange
        const string Input = "Expand this abbreviation: LLM";

        var geminiService = new GeminiTextGenerationService(this.GetModel(), this.GetApiKey());

        // Act
        var response = await geminiService.GetTextContentAsync(Input);

        // Assert
        Assert.NotNull(response.Text);
        Assert.Contains("Large Language Model", response.Text, StringComparison.OrdinalIgnoreCase);
    }

    private string GetModel() => this._configuration.GetSection("Gemini:ModelId").Get<string>()!;
    private string GetApiKey() => this._configuration.GetSection("Gemini:ApiKey").Get<string>()!;
}
