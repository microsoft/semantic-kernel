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
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

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
        var openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        IKernel target = Kernel.Builder
            .WithLoggerFactory(this._logger)
            .WithOpenAITextCompletionService(
                serviceId: openAIConfiguration.ServiceId,
                modelId: openAIConfiguration.ModelId,
                apiKey: openAIConfiguration.ApiKey,
                setAsDefault: true)
            .Build();

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkills(target, "ChatSkill");

        // Act
        SKContext actual = await target.RunAsync(prompt, skill["Chat"]);

        // Assert
        Assert.Contains(expectedAnswerContains, actual.Result, StringComparison.OrdinalIgnoreCase);
    }

    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place Market")]
    public async Task OpenAIChatAsTextTestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        KernelBuilder builder = Kernel.Builder.WithLoggerFactory(this._logger);

        this.ConfigureChatOpenAI(builder);

        IKernel target = builder.Build();

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkills(target, "ChatSkill");

        // Act
        SKContext actual = await target.RunAsync(prompt, skill["Chat"]);

        // Assert
        Assert.Contains(expectedAnswerContains, actual.Result, StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "Skipping while we investigate issue with GitHub actions.")]
    public async Task CanUseOpenAiChatForTextCompletionAsync()
    {
        // Note: we use OpenAi Chat Completion and GPT 3.5 Turbo
        KernelBuilder builder = Kernel.Builder.WithLoggerFactory(this._logger);
        this.ConfigureChatOpenAI(builder);

        IKernel target = builder.Build();

        var func = target.CreateSemanticFunction(
            "List the two planets after '{{$input}}', excluding moons, using bullet points.");

        var result = await func.InvokeAsync("Jupiter");

        Assert.NotNull(result);
        Assert.False(result.ErrorOccurred);
        Assert.Contains("Saturn", result.Result, StringComparison.InvariantCultureIgnoreCase);
        Assert.Contains("Uranus", result.Result, StringComparison.InvariantCultureIgnoreCase);
    }

    [Theory]
    [InlineData(false, "Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    [InlineData(true, "Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    public async Task AzureOpenAITestAsync(bool useChatModel, string prompt, string expectedAnswerContains)
    {
        // Arrange

        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        var builder = Kernel.Builder.WithLoggerFactory(this._logger);

        if (useChatModel)
        {
            this.ConfigureAzureOpenAIChatAsText(builder);
        }
        else
        {
            this.ConfigureAzureOpenAI(builder);
        }

        IKernel target = builder.Build();

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkills(target, "ChatSkill");

        // Act
        SKContext actual = await target.RunAsync(prompt, skill["Chat"]);

        // Assert
        Assert.Null(actual.LastException);
        Assert.False(actual.ErrorOccurred);
        Assert.Contains(expectedAnswerContains, actual.Result, StringComparison.OrdinalIgnoreCase);
    }

    // If the test fails, please note that SK retry logic may not be fully integrated into the underlying code using Azure SDK
    [Theory]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?",
        "Error executing action [attempt 1 of 1]. Reason: Unauthorized. Will retry after 2000ms")]
    public async Task OpenAIHttpRetryPolicyTestAsync(string prompt, string expectedOutput)
    {
        // Arrange
        var retryConfig = new HttpRetryConfig();
        retryConfig.RetryableStatusCodes.Add(HttpStatusCode.Unauthorized);

        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        IKernel target = Kernel.Builder
            .WithLoggerFactory(this._testOutputHelper)
            .Configure(c => c.SetDefaultHttpRetryConfig(retryConfig))
            .WithOpenAITextCompletionService(
                serviceId: openAIConfiguration.ServiceId,
                modelId: openAIConfiguration.ModelId,
                apiKey: "INVALID_KEY") // Use an invalid API key to force a 401 Unauthorized response
            .Build();

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkills(target, "SummarizeSkill");

        // Act
        var context = await target.RunAsync(prompt, skill["Summarize"]);

        // Assert
        Assert.Contains(expectedOutput, this._testOutputHelper.GetLogs(), StringComparison.OrdinalIgnoreCase);
    }

    // If the test fails, please note that SK retry logic may not be fully integrated into the underlying code using Azure SDK
    [Theory]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?",
        "Error executing action [attempt 1 of 1]. Reason: Unauthorized. Will retry after 2000ms")]
    public async Task AzureOpenAIHttpRetryPolicyTestAsync(string prompt, string expectedOutput)
    {
        // Arrange
        var retryConfig = new HttpRetryConfig();
        retryConfig.RetryableStatusCodes.Add(HttpStatusCode.Unauthorized);
        KernelBuilder builder = Kernel.Builder
            .WithLoggerFactory(this._testOutputHelper)
            .Configure(c => c.SetDefaultHttpRetryConfig(retryConfig));

        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        // Use an invalid API key to force a 401 Unauthorized response
        builder.WithAzureTextCompletionService(
            deploymentName: azureOpenAIConfiguration.DeploymentName,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: "INVALID_KEY");

        IKernel target = builder.Build();

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkills(target, "SummarizeSkill");

        // Act
        var context = await target.RunAsync(prompt, skill["Summarize"]);

        // Assert
        Assert.Contains(expectedOutput, this._testOutputHelper.GetLogs(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task OpenAIHttpInvalidKeyShouldReturnErrorDetailAsync()
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        // Use an invalid API key to force a 401 Unauthorized response
        IKernel target = Kernel.Builder
            .WithOpenAITextCompletionService(
                modelId: openAIConfiguration.ModelId,
                apiKey: "INVALID_KEY",
                serviceId: openAIConfiguration.ServiceId)
            .Build();

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkills(target, "SummarizeSkill");

        // Act
        var context = await target.RunAsync("Any", skill["Summarize"]);

        // Assert
        Assert.True(context.ErrorOccurred);
        Assert.IsType<AIException>(context.LastException);
        Assert.Equal(AIException.ErrorCodes.AccessDenied, ((AIException)context.LastException).ErrorCode);
        Assert.Contains("The request is not authorized, HTTP status: 401", ((AIException)context.LastException).Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task AzureOpenAIHttpInvalidKeyShouldReturnErrorDetailAsync()
    {
        // Arrange
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        IKernel target = Kernel.Builder
            .WithLoggerFactory(this._testOutputHelper)
            .WithAzureTextCompletionService(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: "INVALID_KEY",
                serviceId: azureOpenAIConfiguration.ServiceId)
            .Build();

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkills(target, "SummarizeSkill");

        // Act
        var context = await target.RunAsync("Any", skill["Summarize"]);

        // Assert
        Assert.True(context.ErrorOccurred);
        Assert.IsType<AIException>(context.LastException);
        Assert.Equal(AIException.ErrorCodes.AccessDenied, ((AIException)context.LastException).ErrorCode);
        Assert.Contains("The request is not authorized, HTTP status: 401", ((AIException)context.LastException).Message, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task AzureOpenAIHttpExceededMaxTokensShouldReturnErrorDetailAsync()
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        // Arrange
        IKernel target = Kernel.Builder
            .WithLoggerFactory(this._testOutputHelper)
            .WithAzureTextCompletionService(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey,
                serviceId: azureOpenAIConfiguration.ServiceId)
            .Build();

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkills(target, "SummarizeSkill");

        // Act
        // Assert
        await Assert.ThrowsAsync<AIException>(() => skill["Summarize"].InvokeAsync(string.Join('.', Enumerable.Range(1, 40000))));
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
            "Given a json input and a request. Apply the request on the json input and return the result. " +
            $"Put the result in between <result></result> tags{lineEnding}" +
            $"Input:{lineEnding}{{\"name\": \"John\", \"age\": 30}}{lineEnding}{lineEnding}Request:{lineEnding}name";

        const string ExpectedAnswerContains = "<result>John</result>";

        IKernel target = Kernel.Builder.WithLoggerFactory(this._logger).Build();

        this._serviceConfiguration[service](target);

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkills(target, "ChatSkill");

        // Act
        SKContext actual = await target.RunAsync(prompt, skill["Chat"]);

        // Assert
        Assert.Contains(ExpectedAnswerContains, actual.Result, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task AzureOpenAIInvokePromptTestAsync()
    {
        // Arrange
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        var builder = Kernel.Builder.WithLoggerFactory(this._logger);
        this.ConfigureAzureOpenAI(builder);
        IKernel target = builder.Build();

        var prompt = "Where is the most famous fish market in Seattle, Washington, USA?";

        // Act
        SKContext actual = await target.InvokeSemanticFunctionAsync(prompt, maxTokens: 150);

        // Assert
        Assert.Null(actual.LastException);
        Assert.False(actual.ErrorOccurred);
        Assert.Contains("Pike Place", actual.Result, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task AzureOpenAIDefaultValueTestAsync()
    {
        // Arrange
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        var builder = Kernel.Builder.WithLoggerFactory(this._logger);
        this.ConfigureAzureOpenAI(builder);
        IKernel target = builder.Build();

        IDictionary<string, ISKFunction> skill = TestHelpers.GetSkills(target, "FunSkill");

        // Act
        SKContext actual = await target.RunAsync(skill["Limerick"]);

        // Assert
        Assert.Null(actual.LastException?.Message);
        Assert.False(actual.ErrorOccurred);
        Assert.Contains("Bob", actual.Result, StringComparison.OrdinalIgnoreCase);
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

    private void ConfigureOpenAI(KernelBuilder kernelBuilder)
    {
        var openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();

        Assert.NotNull(openAIConfiguration);
        Assert.NotNull(openAIConfiguration.ModelId);
        Assert.NotNull(openAIConfiguration.ApiKey);
        Assert.NotNull(openAIConfiguration.ServiceId);

        kernelBuilder.WithOpenAITextCompletionService(
            modelId: openAIConfiguration.ModelId,
            apiKey: openAIConfiguration.ApiKey,
            serviceId: openAIConfiguration.ServiceId,
            setAsDefault: true);
    }

    private void ConfigureChatOpenAI(KernelBuilder kernelBuilder)
    {
        var openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();

        Assert.NotNull(openAIConfiguration);
        Assert.NotNull(openAIConfiguration.ChatModelId);
        Assert.NotNull(openAIConfiguration.ApiKey);
        Assert.NotNull(openAIConfiguration.ServiceId);

        kernelBuilder.WithOpenAIChatCompletionService(
            modelId: openAIConfiguration.ChatModelId,
            apiKey: openAIConfiguration.ApiKey,
            serviceId: openAIConfiguration.ServiceId,
            setAsDefault: true);
    }

    private void ConfigureAzureOpenAI(KernelBuilder kernelBuilder)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.DeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);
        Assert.NotNull(azureOpenAIConfiguration.ApiKey);
        Assert.NotNull(azureOpenAIConfiguration.ServiceId);

        kernelBuilder.WithAzureTextCompletionService(
            deploymentName: azureOpenAIConfiguration.DeploymentName,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey,
            serviceId: azureOpenAIConfiguration.ServiceId,
            setAsDefault: true);
    }

    private void ConfigureAzureOpenAIChatAsText(KernelBuilder kernelBuilder)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.ChatDeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.ApiKey);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);
        Assert.NotNull(azureOpenAIConfiguration.ServiceId);

        kernelBuilder.WithAzureChatCompletionService(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey,
            serviceId: azureOpenAIConfiguration.ServiceId);
    }

    #endregion
}
