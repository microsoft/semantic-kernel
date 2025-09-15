// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.AzureAIInference;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class AzureAIInferenceEmbeddingGeneratorTests(ITestOutputHelper output) : BaseIntegrationTest, IDisposable
{
    private readonly XunitLogger<Kernel> _loggerFactory = new(output);
    private readonly RedirectOutput _testOutputHelper = new(output);
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureAIInferenceEmbeddingGeneratorTests>()
        .Build();

    [Theory(Skip = "For manual verification only")]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?")]
    public async Task InvokeGenerateAsync(string prompt)
    {
        // Arrange
        var config = this._configuration.GetSection("AzureAIInferenceEmbeddings").Get<AzureAIInferenceEmbeddingsConfiguration>();
        Assert.NotNull(config);

        IEmbeddingGenerator<string, Embedding<float>> sut = this.CreateEmbeddingGenerator(config);

        // Act
        var result = await sut.GenerateAsync([prompt]);

        // Assert
        Assert.Single(result);
        Assert.Equal(1536, result[0].Vector.Length);
    }

    private IEmbeddingGenerator<string, Embedding<float>> CreateEmbeddingGenerator(AzureAIInferenceEmbeddingsConfiguration config)
    {
        var serviceCollection = new ServiceCollection();
        serviceCollection.AddSingleton(this._loggerFactory);

        Assert.NotNull(config.ModelId);

        if (config.ApiKey is not null)
        {
            serviceCollection.AddAzureAIInferenceEmbeddingGenerator(
                modelId: config.ModelId,
                endpoint: config.Endpoint,
                apiKey: config.ApiKey);
        }
        else
        {
            serviceCollection.AddAzureAIInferenceEmbeddingGenerator(
                modelId: config.ModelId,
                endpoint: config.Endpoint,
                credential: new AzureCliCredential());
        }

        var serviceProvider = serviceCollection.BuildServiceProvider();

        return serviceProvider.GetRequiredService<IEmbeddingGenerator<string, Embedding<float>>>();
    }

    public void Dispose()
    {
        this._loggerFactory.Dispose();
        this._testOutputHelper.Dispose();
    }
}
