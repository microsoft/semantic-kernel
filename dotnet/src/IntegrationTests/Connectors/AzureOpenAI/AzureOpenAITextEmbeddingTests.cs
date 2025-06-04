// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Embeddings;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureOpenAI;

[Obsolete("Temporary Tests for Obsolete AzureOpenAITextEmbeddingGenerationService")]
public sealed class AzureOpenAITextEmbeddingTests
{
    public AzureOpenAITextEmbeddingTests()
    {
        var config = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(config);
        this._azureOpenAIConfiguration = config;
    }

    [Theory]
    [InlineData("test sentence")]
    public async Task AzureOpenAITestAsync(string testInputString)
    {
        // Arrange
        var embeddingGenerator = new AzureOpenAITextEmbeddingGenerationService(
            deploymentName: this._azureOpenAIConfiguration.DeploymentName,
            endpoint: this._azureOpenAIConfiguration.Endpoint,
            credential: new AzureCliCredential());

        // Act
        var singleResult = await embeddingGenerator.GenerateEmbeddingAsync(testInputString);
        var batchResult = await embeddingGenerator.GenerateEmbeddingsAsync([testInputString]);

        // Assert
        Assert.Equal(AdaVectorLength, singleResult.Length);
        Assert.Single(batchResult);
    }

    [Theory]
    [InlineData(null, 3072)]
    [InlineData(1024, 1024)]
    public async Task AzureOpenAITextEmbeddingGenerationWithDimensionsAsync(int? dimensions, int expectedVectorLength)
    {
        // Arrange
        const string TestInputString = "test sentence";

        var embeddingGenerator = new AzureOpenAITextEmbeddingGenerationService(
            deploymentName: "text-embedding-3-large",
            endpoint: this._azureOpenAIConfiguration.Endpoint,
            credential: new AzureCliCredential(),
            dimensions: dimensions);

        // Act
        var result = await embeddingGenerator.GenerateEmbeddingAsync(TestInputString);

        // Assert
        Assert.Equal(expectedVectorLength, result.Length);
    }

    private readonly AzureOpenAIConfiguration _azureOpenAIConfiguration;

    private const int AdaVectorLength = 1536;

    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureOpenAITextEmbeddingTests>()
        .Build();
}

public sealed class AzureOpenAIEmbeddingGeneratorTests
{
    public AzureOpenAIEmbeddingGeneratorTests()
    {
        var config = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(config);
        this._azureOpenAIConfiguration = config;
    }

    [Theory]
    [InlineData("test sentence")]
    public async Task AzureOpenAITestAsync(string testInputString)
    {
        // Arrange
        var embeddingGenerator = Kernel.CreateBuilder()
            .AddAzureOpenAIEmbeddingGenerator(
                deploymentName: this._azureOpenAIConfiguration.DeploymentName,
                endpoint: this._azureOpenAIConfiguration.Endpoint,
                credential: new AzureCliCredential())
            .Build()
            .GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Act
        var singleResult = await embeddingGenerator.GenerateAsync(testInputString);
        var batchResult = await embeddingGenerator.GenerateAsync([testInputString]);

        // Assert
        Assert.Equal(AdaVectorLength, singleResult.Vector.Length);
        Assert.Single(batchResult);
    }

    [Theory]
    [InlineData(null, 3072)]
    [InlineData(1024, 1024)]
    public async Task AzureOpenAITextEmbeddingGenerationWithDimensionsAsync(int? dimensions, int expectedVectorLength)
    {
        // Arrange
        const string TestInputString = "test sentence";

        var embeddingGenerator = Kernel.CreateBuilder()
            .AddAzureOpenAIEmbeddingGenerator(
                deploymentName: "text-embedding-3-large",
                endpoint: this._azureOpenAIConfiguration.Endpoint,
                credential: new AzureCliCredential(),
                dimensions: dimensions)
            .Build()
            .GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Act
        var result = await embeddingGenerator.GenerateAsync(TestInputString);

        // Assert
        Assert.Equal(expectedVectorLength, result.Vector.Length);
    }

    private readonly AzureOpenAIConfiguration _azureOpenAIConfiguration;

    private const int AdaVectorLength = 1536;

    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureOpenAIEmbeddingGeneratorTests>()
        .Build();
}
