// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using Microsoft.SemanticKernel.Embeddings;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTestsV2.Connectors.AzureOpenAI;

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
            this._azureOpenAIConfiguration.DeploymentName,
            this._azureOpenAIConfiguration.Endpoint,
            this._azureOpenAIConfiguration.ApiKey);

        // Act
        var singleResult = await embeddingGenerator.GenerateEmbeddingAsync(testInputString);
        var batchResult = await embeddingGenerator.GenerateEmbeddingsAsync([testInputString, testInputString, testInputString]);

        // Assert
        Assert.Equal(AdaVectorLength, singleResult.Length);
        Assert.Equal(3, batchResult.Count);
    }

    [Theory]
    [InlineData(null, 3072)]
    [InlineData(1024, 1024)]
    public async Task AzureOpenAIWithDimensionsAsync(int? dimensions, int expectedVectorLength)
    {
        // Arrange
        const string TestInputString = "test sentence";

        var embeddingGenerator = new AzureOpenAITextEmbeddingGenerationService(
            "text-embedding-3-large",
            this._azureOpenAIConfiguration.Endpoint,
            this._azureOpenAIConfiguration.ApiKey,
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
