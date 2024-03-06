// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MistralAI;

/// <summary>
/// Integration tests for <see cref="MistralAITextEmbeddingGenerationService"/>.
/// </summary>
public sealed class MistralAITextEmbeddingTests
{
    private readonly IConfigurationRoot _configuration;

    public MistralAITextEmbeddingTests()
    {
        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<MistralAITextEmbeddingTests>()
            .Build();
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task MistralAIGenerateEmbeddingsAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:EmbeddingModel"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        var service = new MistralAITextEmbeddingGenerationService(model!, apiKey!);

        // Act
        List<string> data = new() { "Hello", "world" };
        var response = await service.GenerateEmbeddingsAsync(data);

        // Assert
        Assert.NotNull(response);
        Assert.Equal(2, response.Count);
        Assert.Equal(1024, response[0].Length);
        Assert.Equal(1024, response[1].Length);
    }
}
