// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Reliability;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

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

        this._serviceConfiguration.Add(AIServiceType.OpenAI, this.ConfigureOpenAI);
        this._serviceConfiguration.Add(AIServiceType.AzureOpenAI, this.ConfigureAzureOpenAI);
    }

    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place Market")]
    public async Task OpenAITestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        IKernel target = Kernel.Builder.WithLogger(this._logger).Build();

        this.ConfigureOpenAI(target);

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkill("ChatSkill", target);

        // Act
        SKContext actual = await target.RunAsync(prompt, skill["Chat"]);

        // Assert
        Assert.Contains(expectedAnswerContains, actual.Result, StringComparison.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    public async Task AzureOpenAITestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        IKernel target = Kernel.Builder.WithLogger(this._logger).Build();

        this.ConfigureAzureOpenAI(target);

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkill("ChatSkill", target);

        // Act
        SKContext actual = await target.RunAsync(prompt, skill["Chat"]);

        // Assert
        Assert.Empty(actual.LastErrorDescription);
        Assert.False(actual.ErrorOccurred);
        Assert.Contains(expectedAnswerContains, actual.Result, StringComparison.OrdinalIgnoreCase);
    }

    [Theory(Skip = "Retry logic needs to be refactored to work with Azure SDK")]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?",
        "Error executing action [attempt 1 of 1]. Reason: Unauthorized. Will retry after 2000ms")]
    public async Task OpenAIHttpRetryPolicyTestAsync(string prompt, string expectedOutput)
    {
        // Arrange
        var retryConfig = new HttpRetryConfig();
        retryConfig.RetryableStatusCodes.Add(HttpStatusCode.Unauthorized);
        IKernel target = Kernel.Builder.WithLogger(this._testOutputHelper).Configure(c => c.SetDefaultHttpRetryConfig(retryConfig)).Build();

        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        // Use an invalid API key to force a 401 Unauthorized response
        target.Config.AddOpenAITextCompletionService(
            serviceId: openAIConfiguration.ServiceId,
            modelId: openAIConfiguration.ModelId,
            apiKey: "INVALID_KEY");

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkill("SummarizeSkill", target);

        // Act
        var context = await target.RunAsync(prompt, skill["Summarize"]);

        // Assert
        Assert.Contains(expectedOutput, this._testOutputHelper.GetLogs(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task OpenAIHttpInvalidKeyShouldReturnErrorDetailAsync()
    {
        // Arrange
        IKernel target = Kernel.Builder.WithLogger(this._testOutputHelper).Build();

        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        // Use an invalid API key to force a 401 Unauthorized response
        target.Config.AddOpenAITextCompletionService(
            serviceId: openAIConfiguration.ServiceId,
            modelId: openAIConfiguration.ModelId,
            apiKey: "INVALID_KEY");

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkill("SummarizeSkill", target);

        // Act
        var context = await target.RunAsync("Any", skill["Summarize"]);

        // Assert
        Assert.True(context.ErrorOccurred);
        Assert.IsType<AIException>(context.LastException);
        Assert.Contains("Incorrect API key provided", ((AIException)context.LastException).Detail, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task AzureOpenAIHttpInvalidKeyShouldReturnErrorDetailAsync()
    {
        // Arrange
        IKernel target = Kernel.Builder.WithLogger(this._testOutputHelper).Build();

        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);

        target.Config.AddAzureTextCompletionService(
            serviceId: azureOpenAIConfiguration.ServiceId,
            deploymentName: azureOpenAIConfiguration.DeploymentName,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: "INVALID_KEY");

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkill("SummarizeSkill", target);

        // Act
        var context = await target.RunAsync("Any", skill["Summarize"]);

        // Assert
        Assert.True(context.ErrorOccurred);
        Assert.IsType<AIException>(context.LastException);
        Assert.Contains("provide a valid key", ((AIException)context.LastException).Detail, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task AzureOpenAIHttpExceededMaxTokensShouldReturnErrorDetailAsync()
    {
        // Arrange
        IKernel target = Kernel.Builder.WithLogger(this._testOutputHelper).Build();

        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);

        target.Config.AddAzureTextCompletionService(
            serviceId: azureOpenAIConfiguration.ServiceId,
            deploymentName: azureOpenAIConfiguration.DeploymentName,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey);

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkill("SummarizeSkill", target);

        // Act
        var context = await skill["Summarize"].InvokeAsync(string.Join('.', Enumerable.Range(1, 40000)));

        // Assert
        Assert.True(context.ErrorOccurred);
        Assert.IsType<AIException>(context.LastException);
        Assert.Contains("maximum context length is", ((AIException)context.LastException).Detail, StringComparison.OrdinalIgnoreCase);
    }

    [Theory(Skip = "This test is for manual verification.")]
    [InlineData("\n", AIServiceType.OpenAI)]
    [InlineData("\r\n", AIServiceType.OpenAI)]
    [InlineData("\n", AIServiceType.AzureOpenAI)]
    [InlineData("\r\n", AIServiceType.AzureOpenAI)]
    public async Task CompletionWithDifferentLineEndingsAsync(string lineEnding, AIServiceType service)
    {
        // Arrange
        var prompt =
            $"Given a json input and a request. Apply the request on the json input and return the result. " +
            $"Put the result in between <result></result> tags{lineEnding}" +
            $"Input:{lineEnding}{{\"name\": \"John\", \"age\": 30}}{lineEnding}{lineEnding}Request:{lineEnding}name";

        const string expectedAnswerContains = "<result>John</result>";

        IKernel target = Kernel.Builder.WithLogger(this._logger).Build();

        this._serviceConfiguration[service](target);

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkill("ChatSkill", target);

        // Act
        SKContext actual = await target.RunAsync(prompt, skill["Chat"]);

        // Assert
        Assert.Contains(expectedAnswerContains, actual.Result, StringComparison.OrdinalIgnoreCase);
    }

    #region internals

    private readonly XunitLogger<Kernel> _logger;
    private readonly RedirectOutput _testOutputHelper;

    private readonly Dictionary<AIServiceType, Action<IKernel>> _serviceConfiguration = new();

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

    private void ConfigureOpenAI(IKernel kernel)
    {
        var openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();

        Assert.NotNull(openAIConfiguration);

        kernel.Config.AddOpenAITextCompletionService(
            serviceId: openAIConfiguration.ServiceId,
            modelId: openAIConfiguration.ModelId,
            apiKey: openAIConfiguration.ApiKey);

        kernel.Config.SetDefaultTextCompletionService(openAIConfiguration.ServiceId);
    }

    private void ConfigureAzureOpenAI(IKernel kernel)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);

        kernel.Config.AddAzureTextCompletionService(
            serviceId: azureOpenAIConfiguration.ServiceId,
            deploymentName: azureOpenAIConfiguration.DeploymentName,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey);

        kernel.Config.SetDefaultTextCompletionService(azureOpenAIConfiguration.ServiceId);
    }

    #endregion
}
