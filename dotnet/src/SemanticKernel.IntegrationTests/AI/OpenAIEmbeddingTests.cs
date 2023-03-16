// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.OpenAI.Services;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.AI;

public sealed class OpenAIEmbeddingTests : IDisposable
{
    private const int AdaVectorLength = 1536;
    private readonly IConfigurationRoot _configuration;

    public OpenAIEmbeddingTests(ITestOutputHelper output)
    {
        this._testOutputHelper = new RedirectOutput(output);
        Console.SetOut(this._testOutputHelper);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAIEmbeddingTests>()
            .Build();
    }

    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("test sentence")]
    public async Task OpenAITestAsync(string testInputString)
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAIEmbeddings").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        OpenAITextEmbeddings embeddingGenerator = new OpenAITextEmbeddings(openAIConfiguration.ModelId, openAIConfiguration.ApiKey);

        // Act
        var singleResult = await embeddingGenerator.GenerateEmbeddingAsync(testInputString);
        var batchResult = await embeddingGenerator.GenerateEmbeddingsAsync(new List<string> { testInputString, testInputString, testInputString });

        // Assert
        Assert.Equal(AdaVectorLength, singleResult.Count);
        Assert.Equal(3, batchResult.Count);

        embeddingGenerator.Dispose();
    }

    [Theory]
    [InlineData("test sentence")]
    public async Task AzureOpenAITestAsync(string testInputString)
    {
        // Arrange
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureTextEmbeddings embeddingGenerator = new AzureTextEmbeddings(azureOpenAIConfiguration.DeploymentName,
            azureOpenAIConfiguration.Endpoint,
            azureOpenAIConfiguration.ApiKey,
            "2022-12-01");

        // Act
        var singleResult = await embeddingGenerator.GenerateEmbeddingAsync(testInputString);
        var batchResult = await embeddingGenerator.GenerateEmbeddingsAsync(new List<string> { testInputString, testInputString, testInputString });

        // Assert
        Assert.Equal(AdaVectorLength, singleResult.Count);
        Assert.Equal(3, batchResult.Count);

        embeddingGenerator.Dispose();
    }

    #region internals

    private readonly RedirectOutput _testOutputHelper;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~OpenAIEmbeddingTests()
    {
        this.Dispose(false);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._testOutputHelper.Dispose();
        }
    }

    #endregion
}
