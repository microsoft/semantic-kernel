// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Azure;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Reliability.Basic;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

public sealed class AzureOpenAICompletionTests : IDisposable
{
    private readonly IConfigurationRoot _configuration;
    private readonly XunitLogger<Kernel> _logger;
    private readonly RedirectOutput _testOutputHelper;

    public AzureOpenAICompletionTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<Kernel>(output);
        this._testOutputHelper = new RedirectOutput(output);
        Console.SetOut(this._testOutputHelper);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<AzureOpenAICompletionTests>()
            .Build();
    }

    [Theory]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?")]
    public async Task AzureOpenAIChatNoHttpRetryPolicyTestShouldThrowAsync(string prompt)
    {
        // Arrange
        var configuration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(configuration);

        var httpRetryConfig = new BasicRetryConfig { MaxRetryCount = 0 };
        BasicHttpRetryHandlerFactory defaultHttpRetryHandlerFactory = new(httpRetryConfig);

        var target = new KernelBuilder()
             .WithLoggerFactory(this._logger)
             .WithAzureChatCompletionService(configuration.ChatDeploymentName!, configuration.Endpoint, configuration.ApiKey)
             .WithHttpHandlerFactory(defaultHttpRetryHandlerFactory)
             .Build();

        // Act
        var func = target.CreateSemanticFunction(prompt);

        var exception = await Assert.ThrowsAsync<HttpOperationException>(() => func.InvokeAsync(string.Empty, requestSettings: new { MaxTokens = 1000000, Temperature = 0.5, TopP = 0.5 }));

        // Assert
        Assert.NotNull(exception);
    }

    [Theory]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?")]
    public async Task AzureOpenAIChatNoHttpRetryPolicyCustomClientShouldThrowAsync(string prompt)
    {
        // Arrange
        var configuration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(configuration);

        var clientOptions = new OpenAIClientOptions();
        clientOptions.Retry.MaxRetries = 0;
        clientOptions.Retry.NetworkTimeout = TimeSpan.FromSeconds(10);

        var openAIClient = new OpenAIClient(new Uri(configuration.Endpoint), new AzureKeyCredential(configuration.ApiKey), clientOptions);

        var target = new KernelBuilder()
             .WithLoggerFactory(this._logger)
             .WithAzureChatCompletionService(configuration.ChatDeploymentName!, openAIClient)
             .Build();

        // Act
        var func = target.CreateSemanticFunction(prompt);

        var exception = await Assert.ThrowsAsync<HttpOperationException>(() => func.InvokeAsync(string.Empty, requestSettings: new { MaxTokens = 1000000, Temperature = 0.5, TopP = 0.5 }));

        // Assert
        Assert.NotNull(exception);
    }

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~AzureOpenAICompletionTests()
    {
        this.Dispose(false);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._logger.Dispose();
            this._testOutputHelper.Dispose();
        }
    }
}
