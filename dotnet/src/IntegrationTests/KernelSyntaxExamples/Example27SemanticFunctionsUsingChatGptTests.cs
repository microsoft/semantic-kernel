// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit.Abstractions;
using Xunit;

namespace SemanticKernel.IntegrationTests.KernelSyntaxExamples;

public sealed class Example27SemanticFunctionsUsingChatGptTests : IDisposable
{
    public Example27SemanticFunctionsUsingChatGptTests(ITestOutputHelper output)
    {
        this._logger = NullLogger.Instance;
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddUserSecrets<Example27SemanticFunctionsUsingChatGptTests>()
            .AddEnvironmentVariables()
            .Build();

        string? bingApiKeyCandidate = this._configuration["Bing:ApiKey"];
        Assert.NotNull(bingApiKeyCandidate);
        this._bingApiKey = bingApiKeyCandidate;
    }

    [Fact]
    public async Task CanRunExampleAsync()
    {
        // Note: we use Chat Completion and GPT 3.5 Turbo
        IKernel kernel = this.InitializeGpt35Kernel(); //new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        var func = kernel.CreateSemanticFunction(
            "List the two planets closest to '{{$input}}', excluding moons, using bullet points.");

        var result = await func.InvokeAsync("Jupiter");

        Assert.NotNull(result);
        Assert.False(result.ErrorOccurred, result.LastErrorDescription);
        Assert.Contains("Saturn", result.Result);
        Assert.Contains("Uranus", result.Result);
    }

    private IKernel InitializeGpt35Kernel()
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        //kernel.Config.AddAzureChatCompletionService("gpt-35-turbo", "https://....openai.azure.com/", "...API KEY...");

        var builder = Kernel.Builder
            .WithLogger(this._testOutputHelper)
            .Configure(config =>
            {
                config.AddAzureChatCompletionService(
                    //deploymentName: azureOpenAIConfiguration.DeploymentName,
                    deploymentName: "gpt-35-turbo",
                    endpoint: azureOpenAIConfiguration.Endpoint,
                    apiKey: azureOpenAIConfiguration.ApiKey);
            });

        //var builder = Kernel.Builder
        //    .WithLogger(this._logger)
        //    .Configure(config =>
        //    {
        //        config.AddOpenAIChatCompletionService("gpt-3.5-turbo", openAIConfiguration.ApiKey);
        //    });

        var kernel = builder.Build();
        return kernel;
    }

    private readonly ILogger _logger;
    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;
    private string _bingApiKey;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~Example27SemanticFunctionsUsingChatGptTests()
    {
        this.Dispose(false);
    }

    private void Dispose(bool disposing)
    {
        if (disposing)
        {
            if (this._logger is IDisposable ld)
            {
                ld.Dispose();
            }

            this._testOutputHelper.Dispose();
        }
    }
}
