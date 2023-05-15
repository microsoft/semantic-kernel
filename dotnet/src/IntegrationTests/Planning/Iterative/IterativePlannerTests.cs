// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Skills.Web.Bing;
using Microsoft.SemanticKernel.Skills.Web;
using Planning.IterativePlanner;
using SemanticKernel.IntegrationTests.Fakes;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planning.Iterative;

public sealed class IterativePlannerTests : IDisposable
{
    public IterativePlannerTests(ITestOutputHelper output)
    {
        this._logger = NullLogger.Instance; 
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<IterativePlannerTests>()
            .Build();

        string? bingApiKeyCandidate = this._configuration["Bing:ApiKey"];
        Assert.NotNull(bingApiKeyCandidate);
        this._bingApiKey = bingApiKeyCandidate;
    }

    [Fact]
    public async Task CanExecuteSimpleIterativePlanAsync()
    {
        // Arrange
        IKernel kernel = this.InitializeKernel();
        var plan = new IterativePlanner(kernel, 1);
        var goal = "Who is Leo DiCaprio's girlfriend? What is her current age raised to the 0.43 power?";

        // Act
        var result = await plan.ExecutePlanAsync(goal);

        //// Assert
        //Assert.NotNull(result);
        //Assert.Equal(
        //    $"Sent email to: something@email.com. Body: Roses are red, violets are blue, Roses are red, violets are blue, Roses are red, violets are blue, PlanInput is hard, so is this test. is hard, so is this test. is hard, so is this test.",
        //    result.Result);
    }

    private IKernel InitializeKernel(bool useEmbeddings = false)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        var builder = Kernel.Builder
            .WithLogger(this._logger)
            .Configure(config =>
            {
                config.AddAzureTextCompletionService(
                    deploymentName: azureOpenAIConfiguration.DeploymentName,
                    endpoint: azureOpenAIConfiguration.Endpoint,
                    apiKey: azureOpenAIConfiguration.ApiKey);

                if (useEmbeddings)
                {
                    config.AddAzureTextEmbeddingGenerationService(
                        deploymentName: azureOpenAIEmbeddingsConfiguration.DeploymentName,
                        endpoint: azureOpenAIEmbeddingsConfiguration.Endpoint,
                        apiKey: azureOpenAIEmbeddingsConfiguration.ApiKey);
                }
            });

        if (useEmbeddings)
        {
            builder = builder.WithMemoryStorage(new VolatileMemoryStore());
        }

        var kernel = builder.Build();

        _ = kernel.ImportSkill(new EmailSkillFake());

        using BingConnector connector = new(this._bingApiKey);

        var webSearchEngineSkill = new WebSearchEngineSkill(connector);

        kernel.ImportSkill(webSearchEngineSkill, "WebSearch");

        kernel.ImportSkill(new LanguageCalculatorSkill(kernel), "calculator");

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

    ~IterativePlannerTests()
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
