// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.MistralAI;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.MistralAI;

/// <summary>
/// Integration tests for <see cref="MistralAIEmbeddingGenerator"/>.
/// </summary>
public sealed class MistralAIEmbeddingGeneratorTests
{
    private readonly IConfigurationRoot _configuration;

    public MistralAIEmbeddingGeneratorTests()
    {
        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<MistralAIEmbeddingGeneratorTests>()
            .Build();
    }

    [Fact(Skip = "This test is for manual verification.")]
    public async Task MistralAIGenerateEmbeddingsAsync()
    {
        // Arrange
        var model = this._configuration["MistralAI:EmbeddingModelId"];
        var apiKey = this._configuration["MistralAI:ApiKey"];
        using var service = new MistralAIEmbeddingGenerator(model!, apiKey!);

        // Act
        List<string> data = ["Hello", "world"];
        var response = await service.GenerateAsync(data);

        // Assert
        Assert.NotNull(response);
        Assert.Equal(2, response.Count);
        Assert.Equal(1024, response[0].Vector.Length);
        Assert.Equal(1024, response[1].Vector.Length);
    }
}
