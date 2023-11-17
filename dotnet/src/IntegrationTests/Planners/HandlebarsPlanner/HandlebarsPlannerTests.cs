// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planners.Handlebars;
using SemanticKernel.IntegrationTests.Fakes;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planners.HandlebarsPlanner;

public sealed class HandlebarsPlannerTests : IDisposable
{
    public HandlebarsPlannerTests(ITestOutputHelper output)
    {
        this._logger = NullLoggerFactory.Instance;
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<HandlebarsPlannerTests>()
            .Build();
    }

    [Theory]
    [InlineData(true, "Write a joke and send it in an e-mail to Kai.", "SendEmail", "test")]
    public async Task CreatePlanFunctionFlowAsync(bool useChatModel, string prompt, string expectedFunction, string expectedPlugin)
    {
        // Arrange
        bool useEmbeddings = false;
        Kernel kernel = this.InitializeKernel(useEmbeddings, useChatModel);
        kernel.ImportPluginFromObject(new EmailPluginFake(), expectedPlugin);
        TestHelpers.ImportSamplePlugins(kernel, "FunPlugin");

        var planner = new Microsoft.SemanticKernel.Planners.Handlebars.HandlebarsPlanner(kernel);

        // Act
        var plan = await planner.CreatePlanAsync(prompt);

        // Assert expected function
        Assert.Contains(
            $"{expectedPlugin}{HandlebarsTemplateEngineExtensions.ReservedNameDelimiter}{expectedFunction}",
            plan.ToString(),
            StringComparison.CurrentCulture
        );
    }

    [RetryTheory]
    [InlineData("Write a novel about software development that is 3 chapters long.", "NovelOutline", "WriterPlugin")]
    public async Task CreatePlanWithDefaultsAsync(string prompt, string expectedFunction, string expectedPlugin)
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();
        TestHelpers.ImportSamplePlugins(kernel, "WriterPlugin", "MiscPlugin");

        var planner = new Microsoft.SemanticKernel.Planners.Handlebars.HandlebarsPlanner(kernel);

        // Act
        var plan = await planner.CreatePlanAsync(prompt);

        // Assert
        Assert.Contains(
            $"{expectedPlugin}{HandlebarsTemplateEngineExtensions.ReservedNameDelimiter}{expectedFunction}",
            plan.ToString(),
            StringComparison.CurrentCulture
        );
    }

    private Kernel InitializeKernel(bool useEmbeddings = false, bool useChatModel = true)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        var builder = new KernelBuilder().WithLoggerFactory(this._logger);
        builder.WithRetryBasic();

        if (useChatModel)
        {
            builder.WithAzureOpenAIChatCompletionService(
                deploymentName: azureOpenAIConfiguration.ChatDeploymentName!,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);
        }
        else
        {
            builder.WithAzureTextCompletionService(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);
        }

        if (useEmbeddings)
        {
            builder.WithAzureOpenAITextEmbeddingGenerationService(
                    deploymentName: azureOpenAIEmbeddingsConfiguration.DeploymentName,
                    endpoint: azureOpenAIEmbeddingsConfiguration.Endpoint,
                    apiKey: azureOpenAIEmbeddingsConfiguration.ApiKey);
        }

        var kernel = builder.Build();
        return kernel;
    }

    private readonly ILoggerFactory _logger;
    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~HandlebarsPlannerTests()
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
