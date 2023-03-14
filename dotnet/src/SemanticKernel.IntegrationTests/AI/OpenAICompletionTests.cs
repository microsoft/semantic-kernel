// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.KernelExtensions;
using Microsoft.SemanticKernel.Orchestration;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.AI;

public sealed class OpenAICompletionTests : IDisposable
{
    private readonly IConfigurationRoot _configuration;

    public OpenAICompletionTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<Kernel>(output);
        this._testOutputHelper = new RedirectOutput(output);
        Console.SetOut(this._testOutputHelper);

        // Load configuration
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<OpenAICompletionTests>()
            .Build();
    }

    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place Market")]
    public async Task OpenAITestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        IKernel target = Kernel.Builder.WithLogger(this._logger).Build();

        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        target.Config.AddOpenAICompletionBackend(
            label: openAIConfiguration.Label,
            modelId: openAIConfiguration.ModelId,
            apiKey: openAIConfiguration.ApiKey);

        target.Config.SetDefaultCompletionBackend(openAIConfiguration.Label);

        IDictionary<string, ISKFunction> skill = GetSkill("ChatSkill", target);

        // Act
        SKContext actual = await target.RunAsync(prompt, skill["Chat"]);

        // Assert
        Assert.Contains(expectedAnswerContains, actual.Result, StringComparison.InvariantCultureIgnoreCase);
    }

    [Theory]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    public async Task AzureOpenAITestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        IKernel target = Kernel.Builder.WithLogger(this._logger).Build();

        // OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        // Assert.NotNull(openAIConfiguration);
        AzureOpenAIConfiguration? azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        target.Config.AddAzureOpenAICompletionBackend(
            label: azureOpenAIConfiguration.Label,
            deploymentName: azureOpenAIConfiguration.DeploymentName,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey);

        target.Config.SetDefaultCompletionBackend(azureOpenAIConfiguration.Label);

        IDictionary<string, ISKFunction> skill = GetSkill("ChatSkill", target);

        // Act
        SKContext actual = await target.RunAsync(prompt, skill["Chat"]);

        // Assert
        Assert.Empty(actual.LastErrorDescription);
        Assert.False(actual.ErrorOccurred);
        Assert.Contains(expectedAnswerContains, actual.Result, StringComparison.InvariantCultureIgnoreCase);
    }

    private static IDictionary<string, ISKFunction> GetSkill(string skillName, IKernel target)
    {
        string? currentAssemblyDirectory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        if (string.IsNullOrWhiteSpace(currentAssemblyDirectory))
        {
            throw new InvalidOperationException("Unable to determine current assembly directory.");
        }

        string skillParentDirectory = Path.GetFullPath(Path.Combine(currentAssemblyDirectory, "../../../../../../samples/skills"));

        IDictionary<string, ISKFunction> skill = target.ImportSemanticSkillFromDirectory(skillParentDirectory, skillName);
        return skill;
    }

    #region internals

    private readonly XunitLogger<Kernel> _logger;
    private readonly RedirectOutput _testOutputHelper;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    ~OpenAICompletionTests()
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

    #endregion
}
