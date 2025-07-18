// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

public sealed class OpenAIEmbeddingGeneratorTests
{
    private const int AdaVectorLength = 1536;
    private const string AdaModelId = "text-embedding-ada-002";
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OpenAIEmbeddingGeneratorTests>()
        .Build();

    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("test sentence")]
    public async Task OpenAITestAsync(string testInputString)
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAIEmbeddings").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        var embeddingGenerator = Kernel.CreateBuilder()
            .AddOpenAIEmbeddingGenerator(AdaModelId, openAIConfiguration.ApiKey)
            .Build()
            .GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Act
        var singleResult = await embeddingGenerator.GenerateAsync(testInputString);
        var batchResult = await embeddingGenerator.GenerateAsync([testInputString, testInputString, testInputString]);

        // Assert
        Assert.Equal(AdaVectorLength, singleResult.Vector.Length);
        Assert.Equal(3, batchResult.Count);
    }

    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData(null, 3072)]
    [InlineData(1024, 1024)]
    public async Task OpenAIWithDimensionsAsync(int? dimensions, int expectedVectorLength)
    {
        // Arrange
        const string TestInputString = "test sentence";

        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAIEmbeddings").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        var embeddingGenerator = Kernel.CreateBuilder()
            .AddOpenAIEmbeddingGenerator("text-embedding-3-large", openAIConfiguration.ApiKey, dimensions: dimensions)
            .Build()
            .GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();

        // Act
        var result = await embeddingGenerator.GenerateAsync(TestInputString);

        // Assert
        Assert.Equal(expectedVectorLength, result.Vector.Length);
    }
}
