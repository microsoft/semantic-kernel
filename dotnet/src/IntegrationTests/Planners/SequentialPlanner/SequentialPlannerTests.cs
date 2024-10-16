﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Plugins.Memory;
using SemanticKernel.IntegrationTests.Fakes;
using SemanticKernel.IntegrationTests.TestSettings;
using xRetry;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Planners.Sequential;

public sealed class SequentialPlannerTests : IDisposable
{
    public SequentialPlannerTests(ITestOutputHelper output)
    {
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
    [InlineData(false, "Write a joke and send it in an e-mail to Kai.", "SendEmail", "EmailPluginFake")]
    [InlineData(true, "Write a joke and send it in an e-mail to Kai.", "SendEmail", "EmailPluginFake")]
    public async Task CreatePlanFunctionFlowAsync(bool useChatModel, string prompt, string expectedFunction, string expectedPlugin)
    {
        // Arrange
        bool useEmbeddings = false;
        Kernel kernel = this.InitializeKernel(useEmbeddings, useChatModel);
        kernel.ImportPluginFromType<EmailPluginFake>();
        TestHelpers.ImportSamplePlugins(kernel, "FunPlugin");

        var planner = new SequentialPlanner(kernel);

        // Act
        var plan = await planner.CreatePlanAsync(prompt);

        // Assert
        Assert.Contains(
            plan.Steps,
            step =>
                step.Name.Equals(expectedFunction, StringComparison.OrdinalIgnoreCase) &&
                step.PluginName.Equals(expectedPlugin, StringComparison.OrdinalIgnoreCase));
    }

    [RetryTheory]
    [InlineData("Write a novel about software development that is 3 chapters long.", "NovelOutline", "WriterPlugin", "<!--===ENDPART===-->")]
    public async Task CreatePlanWithDefaultsAsync(string prompt, string expectedFunction, string expectedPlugin, string expectedDefault)
    {
        // Arrange
        Kernel kernel = this.InitializeKernel();
        TestHelpers.ImportSamplePlugins(kernel, "WriterPlugin", "MiscPlugin");

        var planner = new SequentialPlanner(kernel);

        // Act
        var plan = await planner.CreatePlanAsync(prompt);

        // Assert
        Assert.Contains(
            plan.Steps,
            step =>
                step.Name.Equals(expectedFunction, StringComparison.OrdinalIgnoreCase) &&
                step.PluginName.Equals(expectedPlugin, StringComparison.OrdinalIgnoreCase) &&
                step.Parameters["endMarker"].Equals(expectedDefault, StringComparison.OrdinalIgnoreCase));
    }

    [RetryTheory]
    [InlineData("Write a poem and a joke and send it in an e-mail to Kai.", "SendEmail", "EmailPluginFake")]
    public async Task CreatePlanGoalRelevantAsync(string prompt, string expectedFunction, string expectedPlugin)
    {
        // Arrange
        bool useEmbeddings = true;

        Kernel kernel = this.InitializeKernel(useEmbeddings);
        ISemanticTextMemory memory = this.InitializeMemory(kernel.GetService<ITextEmbeddingGeneration>());

        kernel.ImportPluginFromType<EmailPluginFake>();

        // Import all sample plugins available for demonstration purposes.
        TestHelpers.ImportAllSamplePlugins(kernel);

        var planner = new SequentialPlanner(kernel,
            new() { SemanticMemoryConfig = new() { RelevancyThreshold = 0.65, MaxRelevantFunctions = 30, Memory = memory } });

        // Act
        var plan = await planner.CreatePlanAsync(prompt);

        // Assert
        Assert.Contains(
            plan.Steps,
            step =>
                step.Name.Equals(expectedFunction, StringComparison.OrdinalIgnoreCase) &&
                step.PluginName.Equals(expectedPlugin, StringComparison.OrdinalIgnoreCase));
    }

    private Kernel InitializeKernel(bool useEmbeddings = false, bool useChatModel = false)
    {
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        AzureOpenAIConfiguration? azureOpenAIEmbeddingsConfiguration = this._configuration.GetSection("AzureOpenAIEmbeddings").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIEmbeddingsConfiguration);

        IKernelBuilder builder = Kernel.CreateBuilder();

        if (useChatModel)
        {
            builder.Services.AddAzureOpenAIChatCompletion(
                deploymentName: azureOpenAIConfiguration.ChatDeploymentName!,
                endpoint: azureOpenAIConfiguration.Endpoint,
                credentials: new AzureCliCredential());
        }
        else
        {
            builder.Services.AddAzureOpenAITextGeneration(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                endpoint: azureOpenAIConfiguration.Endpoint,
                credentials: new AzureCliCredential());
        }

        if (useEmbeddings)
        {
            builder.Services.AddAzureOpenAITextEmbeddingGeneration(
                    deploymentName: azureOpenAIEmbeddingsConfiguration.DeploymentName,
                    endpoint: azureOpenAIEmbeddingsConfiguration.Endpoint,
                    apiKey: azureOpenAIEmbeddingsConfiguration.ApiKey);
        }

        return builder.Build();
    }

    private ISemanticTextMemory InitializeMemory(ITextEmbeddingGeneration textEmbeddingGeneration)
    {
        var builder = new MemoryBuilder();

        builder.WithMemoryStore(new VolatileMemoryStore());
        builder.WithTextEmbeddingGeneration(textEmbeddingGeneration);

        return builder.Build();
    }

    private readonly RedirectOutput _testOutputHelper;
    private readonly IConfigurationRoot _configuration;

    public void Dispose()
    {
        this._testOutputHelper.Dispose();
    }
}
