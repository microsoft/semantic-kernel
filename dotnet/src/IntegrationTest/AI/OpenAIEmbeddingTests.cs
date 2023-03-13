// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using IntegrationTests.TestSettings;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.OpenAI.Services;
using Microsoft.SemanticKernel.Http;
using Xunit;
using Xunit.Abstractions;

namespace IntegrationTests.AI;

public sealed class OpenAIEmbeddingTests : IDisposable
{
    private const int AdaVectorLength = 1536;
    private readonly IConfigurationRoot _configuration;
    private readonly HttpClientFactory _httpClientFactory;

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
        this._httpClientFactory = new HttpClientFactory();
    }

    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("test sentence")]
    public async Task OpenAITestAsync(string testInputString)
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAIEmbeddings").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        var embeddingGenerator = new BackendServiceFactory(this._httpClientFactory, NullLogger.Instance).CreateEmbeddingGenerator(this.CreateConfig(openAIConfiguration));

        // Act
        var singleResult = await embeddingGenerator.GenerateEmbeddingAsync(testInputString);
        var batchResult = await embeddingGenerator.GenerateEmbeddingsAsync(new List<string> { testInputString, testInputString, testInputString });

        // Assert
        Assert.Equal(AdaVectorLength, singleResult.Count);
        Assert.Equal(3, batchResult.Count);
    }

    [Theory]
    [InlineData("test sentence")]
    public async Task AzureOpenAITestAsync(string testInputString)
    {
        // Arrange
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        var embeddingGenerator = new BackendServiceFactory(this._httpClientFactory, NullLogger.Instance).CreateEmbeddingGenerator(this.CreateConfig(azureOpenAIConfiguration, "2022-12-01"));

        // Act
        var singleResult = await embeddingGenerator.GenerateEmbeddingAsync(testInputString);
        var batchResult = await embeddingGenerator.GenerateEmbeddingsAsync(new List<string> { testInputString, testInputString, testInputString });

        // Assert
        Assert.Equal(AdaVectorLength, singleResult.Count);
        Assert.Equal(3, batchResult.Count);
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
            this._httpClientFactory.Dispose();
        }
    }

    private OpenAIConfig CreateConfig(OpenAIConfiguration config)
    {
        return new OpenAIConfig(config.Label, config.ModelId, config.ApiKey, string.Empty);
    }

    private AzureOpenAIConfig CreateConfig(AzureOpenAIConfiguration config, string apiVersion)
    {
        return new AzureOpenAIConfig(config.Label, config.DeploymentName, config.Endpoint, config.ApiKey, apiVersion);
    }

    #endregion
}
