// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Issues;

public sealed class Issue1050 : IDisposable
{
    public Issue1050(ITestOutputHelper output)
    {
        this._logger = NullLogger.Instance;
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddUserSecrets<Issue1050>()
            .AddEnvironmentVariables()
            .Build();
    }

    [Fact]
    public async Task CanUseOpenAiChatForTextCompletionAsync()
    {
        // Note: we use OpenAi Chat Completion and GPT 3.5 Turbo
        IKernel kernel = this.InitializeOpenAiKernel(); //new KernelBuilder().WithLogger(ConsoleLogger.Log).Build();

        var func = kernel.CreateSemanticFunction(
            "List the two planets closest to '{{$input}}', excluding moons, using bullet points.");

        var result = await func.InvokeAsync("Jupiter");

        Assert.NotNull(result);
        Assert.False(result.ErrorOccurred, result.LastErrorDescription);
        Assert.Contains("Saturn", result.Result);
        Assert.Contains("Uranus", result.Result);
    }

    private IKernel InitializeOpenAiKernel()
    {
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        //kernel.Config.AddAzureChatCompletionService("gpt-35-turbo", "https://....openai.azure.com/", "...API KEY...");

        var builder = Kernel.Builder
            .WithLogger(this._testOutputHelper)
            .Configure(config =>
            {
                config.AddOpenAIChatCompletionService("gpt-3.5-turbo", openAIConfiguration.ApiKey);
            });

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

    ~Issue1050()
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
