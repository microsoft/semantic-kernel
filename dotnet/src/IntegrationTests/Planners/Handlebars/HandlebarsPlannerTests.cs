// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning.Handlebars;
using SemanticKernel.IntegrationTests.Fakes;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planners.Handlebars;

public sealed class HandlebarsPlannerTests : IDisposable
{
    public HandlebarsPlannerTests(ITestOutputHelper output)
    {
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
    [InlineData("Write a joke and send it in an e-mail to Kai.", "SendEmail", "test")]
    public async Task CreatePlanFunctionFlowAsync(string prompt, string expectedFunction, string expectedPlugin)
    {
        // Arrange
        bool useEmbeddings = false;
        var kernel = this.InitializeKernel(useEmbeddings);
        kernel.ImportPluginFromType<EmailPluginFake>(expectedPlugin);
        TestHelpers.ImportSamplePlugins(kernel, "FunPlugin");

        // Act
        var plan = await new HandlebarsPlanner().CreatePlanAsync(kernel, prompt);

        // Assert expected function
        Assert.Contains(
            $"{expectedPlugin}-{expectedFunction}",
            plan.ToString(),
            StringComparison.CurrentCulture
        );
    }

    [RetryTheory]
    [InlineData("Write a novel about software development that is 3 chapters long.", "NovelChapter", "WriterPlugin")]
    public async Task CreatePlanWithDefaultsAsync(string prompt, string expectedFunction, string expectedPlugin)
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();
        TestHelpers.ImportSamplePlugins(kernel, "WriterPlugin", "MiscPlugin");

        // Act
        var plan = await new HandlebarsPlanner().CreatePlanAsync(kernel, prompt);

        // Assert
        Assert.Contains(
            $"{expectedPlugin}-{expectedFunction}",
            plan.ToString(),
            StringComparison.CurrentCulture
        );
    }

    private Kernel InitializeKernel(bool useEmbeddings = false)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        IKernelBuilder builder = Kernel.CreateBuilder();

        builder.Services.AddAzureOpenAIChatCompletion(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey);

        if (useEmbeddings)
        {
            builder.Services.AddAzureOpenAITextEmbeddingGeneration(
                deploymentName: azureOpenAIEmbeddingsConfiguration.DeploymentName,
                modelId: azureOpenAIEmbeddingsConfiguration.EmbeddingModelId,
                endpoint: azureOpenAIEmbeddingsConfiguration.Endpoint,
                apiKey: azureOpenAIEmbeddingsConfiguration.ApiKey);
        }

        return builder.Build();
    }

    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose()
    {
        this._testOutputHelper.Dispose();
    }
}
