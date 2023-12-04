// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Http.Resilience;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Http;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class OpenAICompletionTests : IDisposable
{
    private readonly KernelBuilder _kernelBuilder;
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

        this._kernelBuilder = new KernelBuilder();
    }

    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place Market")]
    public async Task OpenAITestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        var openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        Kernel target = this._kernelBuilder
            .WithLoggerFactory(this._logger)
            .WithOpenAITextCompletion(
                serviceId: openAIConfiguration.ServiceId,
                modelId: openAIConfiguration.ModelId,
                apiKey: openAIConfiguration.ApiKey)
            .Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "ChatPlugin");

        // Act
        FunctionResult actual = await target.InvokeAsync(plugins["ChatPlugin"]["Chat"], prompt);

        // Assert
        Assert.Contains(expectedAnswerContains, actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place Market")]
    public async Task OpenAIChatAsTextTestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        KernelBuilder builder = this._kernelBuilder.WithLoggerFactory(this._logger);

        this.ConfigureChatOpenAI(builder);

        Kernel target = builder.Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "ChatPlugin");

        // Act
        FunctionResult actual = await target.InvokeAsync(plugins["ChatPlugin"]["Chat"], prompt);

        // Assert
        Assert.Contains(expectedAnswerContains, actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "Skipping while we investigate issue with GitHub actions.")]
    public async Task CanUseOpenAiChatForTextCompletionAsync()
    {
        // Note: we use OpenAI Chat Completion and GPT 3.5 Turbo
        KernelBuilder builder = this._kernelBuilder.WithLoggerFactory(this._logger);
        this.ConfigureChatOpenAI(builder);

        Kernel target = builder.Build();

        var func = target.CreateFunctionFromPrompt(
            "List the two planets after '{{$input}}', excluding moons, using bullet points.",
            new OpenAIPromptExecutionSettings());

        var result = await func.InvokeAsync(target, "Jupiter");

        Assert.NotNull(result);
        Assert.Contains("Saturn", result.GetValue<string>(), StringComparison.InvariantCultureIgnoreCase);
        Assert.Contains("Uranus", result.GetValue<string>(), StringComparison.InvariantCultureIgnoreCase);
    }

    [Theory]
    [InlineData(false, "Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    [InlineData(true, "Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    public async Task AzureOpenAIStreamingTestAsync(bool useChatModel, string prompt, string expectedAnswerContains)
    {
        // Arrange
        var builder = this._kernelBuilder.WithLoggerFactory(this._logger);

        if (useChatModel)
        {
            this.ConfigureAzureOpenAIChatAsText(builder);
        }
        else
        {
            this.ConfigureAzureOpenAI(builder);
        }

        Kernel target = builder.Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "ChatPlugin");

        StringBuilder fullResult = new();
        // Act
        await foreach (var content in target.InvokeStreamingAsync<StreamingContentBase>(plugins["ChatPlugin"]["Chat"], prompt))
        {
            fullResult.Append(content);
        };

        // Assert
        Assert.Contains(expectedAnswerContains, fullResult.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData(false, "Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    [InlineData(true, "Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    public async Task AzureOpenAITestAsync(bool useChatModel, string prompt, string expectedAnswerContains)
    {
        // Arrange
        var builder = this._kernelBuilder.WithLoggerFactory(this._logger);

        if (useChatModel)
        {
            this.ConfigureAzureOpenAIChatAsText(builder);
        }
        else
        {
            this.ConfigureAzureOpenAI(builder);
        }

        Kernel target = builder.Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "ChatPlugin");

        // Act
        FunctionResult actual = await target.InvokeAsync(plugins["ChatPlugin"]["Chat"], prompt);

        // Assert
        Assert.Contains(expectedAnswerContains, actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    // If the test fails, please note that SK retry logic may not be fully integrated into the underlying code using Azure SDK
    [Theory]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Resilience event occurred")]
    public async Task OpenAIHttpRetryPolicyTestAsync(string prompt, string expectedOutput)
    {
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        Kernel target = this._kernelBuilder
            .WithLoggerFactory(this._testOutputHelper)
            .WithOpenAITextCompletion(
                serviceId: openAIConfiguration.ServiceId,
                modelId: openAIConfiguration.ModelId,
                apiKey: "INVALID_KEY") // Use an invalid API key to force a 401 Unauthorized response
            .WithServices(c => c.ConfigureHttpClientDefaults(c =>
                {
                    // Use a standard resiliency policy, augmented to retry on 401 Unauthorized for this example
                    c.AddStandardResilienceHandler().Configure(o =>
                    {
                        o.Retry.ShouldHandle = args => ValueTask.FromResult(args.Outcome.Result?.StatusCode is HttpStatusCode.Unauthorized);
                    });
                }))
            .Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");

        // Act
        await Assert.ThrowsAsync<HttpOperationException>(() => target.InvokeAsync(plugins["SummarizePlugin"]["Summarize"], prompt));

        // Assert
        Assert.Contains(expectedOutput, this._testOutputHelper.GetLogs(), StringComparison.OrdinalIgnoreCase);
    }

    // If the test fails, please note that SK retry logic may not be fully integrated into the underlying code using Azure SDK
    [Theory]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Resilience event occurred")]
    public async Task AzureOpenAIHttpRetryPolicyTestAsync(string prompt, string expectedOutput)
    {
        KernelBuilder builder = this._kernelBuilder
            .WithLoggerFactory(this._testOutputHelper);

        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        // Use an invalid API key to force a 401 Unauthorized response
        builder.WithAzureOpenAITextCompletion(
            deploymentName: azureOpenAIConfiguration.DeploymentName,
            modelId: azureOpenAIConfiguration.ModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: "INVALID_KEY");

        builder.WithServices(c => c.ConfigureHttpClientDefaults(c =>
            {
                // Use a standard resiliency policy, augmented to retry on 401 Unauthorized for this example
                c.AddStandardResilienceHandler().Configure(o =>
                {
                    o.Retry.ShouldHandle = args => ValueTask.FromResult(args.Outcome.Result?.StatusCode is HttpStatusCode.Unauthorized);
                });
            }));

        Kernel target = builder.Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");

        // Act
        await Assert.ThrowsAsync<HttpOperationException>(() => target.InvokeAsync(plugins["SummarizePlugin"]["Summarize"], prompt));

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
        Kernel target = this._kernelBuilder
            .WithOpenAITextCompletion(
                modelId: openAIConfiguration.ModelId,
                apiKey: "INVALID_KEY",
                serviceId: openAIConfiguration.ServiceId)
            .Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");

        // Act and Assert
        var ex = await Assert.ThrowsAsync<HttpOperationException>(() => target.InvokeAsync(plugins["SummarizePlugin"]["Summarize"], "Any"));

        Assert.Equal(HttpStatusCode.Unauthorized, ((HttpOperationException)ex).StatusCode);
    }

    [Fact]
    public async Task AzureOpenAIHttpInvalidKeyShouldReturnErrorDetailAsync()
    {
        // Arrange
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        Kernel target = this._kernelBuilder
            .WithLoggerFactory(this._testOutputHelper)
            .WithAzureOpenAITextCompletion(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                modelId: azureOpenAIConfiguration.ModelId,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: "INVALID_KEY",
                serviceId: azureOpenAIConfiguration.ServiceId)
            .Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");

        // Act and Assert
        var ex = await Assert.ThrowsAsync<HttpOperationException>(() => target.InvokeAsync(plugins["SummarizePlugin"]["Summarize"], "Any"));

        Assert.Equal(HttpStatusCode.Unauthorized, ((HttpOperationException)ex).StatusCode);
    }

    [Fact]
    public async Task AzureOpenAIHttpExceededMaxTokensShouldReturnErrorDetailAsync()
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        // Arrange
        Kernel target = this._kernelBuilder
            .WithLoggerFactory(this._testOutputHelper)
            .WithAzureOpenAITextCompletion(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                modelId: azureOpenAIConfiguration.ModelId,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey,
                serviceId: azureOpenAIConfiguration.ServiceId)
            .Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");

        // Act
        // Assert
        await Assert.ThrowsAsync<HttpOperationException>(() => plugins["SummarizePlugin"]["Summarize"].InvokeAsync(target, string.Join('.', Enumerable.Range(1, 40000))));
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

        Kernel target = this._kernelBuilder.WithLoggerFactory(this._logger).Build();

        this._serviceConfiguration[service](target);

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "ChatPlugin");

        // Act
        FunctionResult actual = await target.InvokeAsync(plugins["ChatPlugin"]["Chat"], prompt);

        // Assert
        Assert.Contains(ExpectedAnswerContains, actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task AzureOpenAIInvokePromptTestAsync()
    {
        // Arrange
        var builder = this._kernelBuilder.WithLoggerFactory(this._logger);
        this.ConfigureAzureOpenAI(builder);
        Kernel target = builder.Build();

        var prompt = "Where is the most famous fish market in Seattle, Washington, USA?";

        // Act
        FunctionResult actual = await target.InvokePromptAsync(prompt, new(new OpenAIPromptExecutionSettings() { MaxTokens = 150 }));

        // Assert
        Assert.Contains("Pike Place", actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task AzureOpenAIDefaultValueTestAsync()
    {
        // Arrange
        var builder = this._kernelBuilder.WithLoggerFactory(this._logger);
        this.ConfigureAzureOpenAI(builder);
        Kernel target = builder.Build();

        IReadOnlyKernelPluginCollection plugin = TestHelpers.ImportSamplePlugins(target, "FunPlugin");

        // Act
        FunctionResult actual = await target.InvokeAsync(plugin["FunPlugin"]["Limerick"]);

        // Assert
        Assert.Contains("Bob", actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task MultipleServiceLoadPromptConfigTestAsync()
    {
        // Arrange
        var builder = this._kernelBuilder.WithLoggerFactory(this._logger);
        this.ConfigureAzureOpenAI(builder);
        this.ConfigureInvalidAzureOpenAI(builder);

        Kernel target = builder.Build();

        var prompt = "Where is the most famous fish market in Seattle, Washington, USA?";
        var defaultPromptModel = new PromptTemplateConfig(prompt) { Name = "FishMarket1" };
        var azurePromptModel = PromptTemplateConfig.FromJson(
            @"{
                ""name"": ""FishMarket2"",
                ""execution_settings"": [
                    {
                        ""max_tokens"": 256,
                        ""service_id"": ""azure-text-davinci-003""
                    }
                ]
            }");
        azurePromptModel.Template = prompt;

        var defaultFunc = target.CreateFunctionFromPrompt(defaultPromptModel);
        var azureFunc = target.CreateFunctionFromPrompt(azurePromptModel);

        // Act
        await Assert.ThrowsAsync<HttpOperationException>(() => target.InvokeAsync(defaultFunc));

        FunctionResult azureResult = await target.InvokeAsync(azureFunc);

        // Assert
        Assert.Contains("Pike Place", azureResult.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    #region internals

    private readonly XunitLogger<Kernel> _logger;
    private readonly RedirectOutput _testOutputHelper;

    private readonly Dictionary<AIServiceType, Action<Kernel>> _serviceConfiguration = new();

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

    private void ConfigureChatOpenAI(KernelBuilder kernelBuilder)
    {
        var openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();

        Assert.NotNull(openAIConfiguration);
        Assert.NotNull(openAIConfiguration.ChatModelId);
        Assert.NotNull(openAIConfiguration.ApiKey);
        Assert.NotNull(openAIConfiguration.ServiceId);

        kernelBuilder.WithOpenAIChatCompletion(
            modelId: openAIConfiguration.ChatModelId,
            apiKey: openAIConfiguration.ApiKey,
            serviceId: openAIConfiguration.ServiceId);
    }

    private void ConfigureAzureOpenAI(KernelBuilder kernelBuilder)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.DeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);
        Assert.NotNull(azureOpenAIConfiguration.ApiKey);
        Assert.NotNull(azureOpenAIConfiguration.ServiceId);

        kernelBuilder.WithAzureOpenAITextCompletion(
            deploymentName: azureOpenAIConfiguration.DeploymentName,
            modelId: azureOpenAIConfiguration.ModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey,
            serviceId: azureOpenAIConfiguration.ServiceId);
    }
    private void ConfigureInvalidAzureOpenAI(KernelBuilder kernelBuilder)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.DeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);

        kernelBuilder.WithAzureOpenAITextCompletion(
            deploymentName: azureOpenAIConfiguration.DeploymentName,
            modelId: azureOpenAIConfiguration.ModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: "invalid-api-key",
            serviceId: $"invalid-{azureOpenAIConfiguration.ServiceId}");
    }

    private void ConfigureAzureOpenAIChatAsText(KernelBuilder kernelBuilder)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.ChatDeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.ApiKey);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);
        Assert.NotNull(azureOpenAIConfiguration.ServiceId);

        kernelBuilder.WithAzureOpenAIChatCompletion(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName,
            modelId: azureOpenAIConfiguration.ChatModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey,
            serviceId: azureOpenAIConfiguration.ServiceId);
    }

    #endregion
}
