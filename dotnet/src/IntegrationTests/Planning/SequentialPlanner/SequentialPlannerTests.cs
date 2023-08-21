// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Planning.Sequential;
using SemanticKernel.IntegrationTests.Fakes;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planning.SequentialPlanner;

public sealed class SequentialPlannerTests : IDisposable
{
    public SequentialPlannerTests(ITestOutputHelper output)
    {
        this._logger = NullLoggerFactory.Instance;
        this._testOutputHelper = new RedirectOutput(output);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<SequentialPlannerTests>()
            .Build();
    }

    [Theory]
    [InlineData(false, "Write a joke and send it in an e-mail to Kai.", "SendEmail", "_GLOBAL_FUNCTIONS_")]
    [InlineData(true, "Write a joke and send it in an e-mail to Kai.", "SendEmail", "_GLOBAL_FUNCTIONS_")]
    public async Task CreatePlanFunctionFlowAsync(bool useChatModel, string prompt, string expectedFunction, string expectedSkill)
    {
        // Arrange
        bool useEmbeddings = false;
        IKernel kernel = this.InitializeKernel(useEmbeddings, useChatModel);
        _ = kernel.ImportSkill(new EmailSkillFake());
        TestHelpers.GetSkills(kernel, "FunSkill");

        var planner = new Microsoft.SemanticKernel.Planning.SequentialPlanner(kernel);

        // Act
        var plan = await planner.CreatePlanAsync(prompt);

        // Assert
        Assert.Contains(
            plan.Steps,
            step =>
                step.Name.Equals(expectedFunction, StringComparison.OrdinalIgnoreCase) &&
                step.SkillName.Equals(expectedSkill, StringComparison.OrdinalIgnoreCase));
    }

    [Theory]
    [InlineData("Write a novel about software development that is 3 chapters long.", "NovelOutline", "WriterSkill", "<!--===ENDPART===-->")]
    public async Task CreatePlanWithDefaultsAsync(string prompt, string expectedFunction, string expectedSkill, string expectedDefault)
    {
        // Arrange
        IKernel kernel = this.InitializeKernel();
        TestHelpers.GetSkills(kernel, "WriterSkill");

        var planner = new Microsoft.SemanticKernel.Planning.SequentialPlanner(kernel);

        // Act
        var plan = await planner.CreatePlanAsync(prompt);

        // Assert
        Assert.Contains(
            plan.Steps,
            step =>
                step.Name.Equals(expectedFunction, StringComparison.OrdinalIgnoreCase) &&
                step.SkillName.Equals(expectedSkill, StringComparison.OrdinalIgnoreCase) &&
                step.Parameters["endMarker"].Equals(expectedDefault, StringComparison.OrdinalIgnoreCase));
    }

    [Theory]
    [InlineData("Write a poem or joke and send it in an e-mail to Kai.", "SendEmail", "_GLOBAL_FUNCTIONS_")]
    public async Task CreatePlanGoalRelevantAsync(string prompt, string expectedFunction, string expectedSkill)
    {
        // Arrange
        bool useEmbeddings = true;
        IKernel kernel = this.InitializeKernel(useEmbeddings);
        _ = kernel.ImportSkill(new EmailSkillFake());

        // Import all sample skills available for demonstration purposes.
        TestHelpers.ImportSampleSkills(kernel);

        var planner = new Microsoft.SemanticKernel.Planning.SequentialPlanner(kernel,
            new SequentialPlannerConfig { RelevancyThreshold = 0.65, MaxRelevantFunctions = 30, Memory = kernel.Memory });

        // Act
        var plan = await planner.CreatePlanAsync(prompt);

        // Assert
        Assert.Contains(
            plan.Steps,
            step =>
                step.Name.Equals(expectedFunction, StringComparison.OrdinalIgnoreCase) &&
                step.SkillName.Equals(expectedSkill, StringComparison.OrdinalIgnoreCase));
    }

    private IKernel InitializeKernel(bool useEmbeddings = false, bool useChatModel = false)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        var builder = Kernel.Builder.WithLoggerFactory(this._logger);

        if (useChatModel)
        {
            builder.WithAzureChatCompletionService(
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
            builder.WithAzureTextEmbeddingGenerationService(
                    deploymentName: azureOpenAIEmbeddingsConfiguration.DeploymentName,
                    endpoint: azureOpenAIEmbeddingsConfiguration.Endpoint,
                    apiKey: azureOpenAIEmbeddingsConfiguration.ApiKey)
                .WithMemoryStorage(new VolatileMemoryStore());
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

    ~SequentialPlannerTests()
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
