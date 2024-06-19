// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Http.Resilience;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.OpenAI;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class OpenAICompletionTests(ITestOutputHelper output) : IDisposable
{
    private const string InputParameterName = "input";
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OpenAICompletionTests>()
        .Build();

    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place Market")]
    public async Task OpenAITestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        var openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        Kernel target = this._kernelBuilder
            .AddOpenAITextGeneration(
                serviceId: openAIConfiguration.ServiceId,
                modelId: openAIConfiguration.ModelId,
                apiKey: openAIConfiguration.ApiKey)
            .Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "ChatPlugin");

        // Act
        FunctionResult actual = await target.InvokeAsync(plugins["ChatPlugin"]["Chat"], new() { [InputParameterName] = prompt });

        // Assert
        Assert.Contains(expectedAnswerContains, actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Theory(Skip = "OpenAI will often throttle requests. This test is for manual verification.")]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place Market")]
    public async Task OpenAIChatAsTextTestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        IKernelBuilder builder = this._kernelBuilder;

        this.ConfigureChatOpenAI(builder);

        Kernel target = builder.Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "ChatPlugin");

        // Act
        FunctionResult actual = await target.InvokeAsync(plugins["ChatPlugin"]["Chat"], new() { [InputParameterName] = prompt });

        // Assert
        Assert.Contains(expectedAnswerContains, actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "Skipping while we investigate issue with GitHub actions.")]
    public async Task CanUseOpenAiChatForTextGenerationAsync()
    {
        // Note: we use OpenAI Chat Completion and GPT 3.5 Turbo
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        IKernelBuilder builder = this._kernelBuilder;
        this.ConfigureChatOpenAI(builder);

        Kernel target = builder.Build();

        var func = target.CreateFunctionFromPrompt(
            "List the two planets after '{{$input}}', excluding moons, using bullet points.",
            new OpenAIPromptExecutionSettings());

        var result = await func.InvokeAsync(target, new() { [InputParameterName] = "Jupiter" });

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
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;

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
        await foreach (var content in target.InvokeStreamingAsync<StreamingKernelContent>(plugins["ChatPlugin"]["Chat"], new() { [InputParameterName] = prompt }))
        {
            fullResult.Append(content);
        }

        // Assert
        Assert.Contains(expectedAnswerContains, fullResult.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData(false, "Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    [InlineData(true, "Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    public async Task AzureOpenAITestAsync(bool useChatModel, string prompt, string expectedAnswerContains)
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;

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
        FunctionResult actual = await target.InvokeAsync(plugins["ChatPlugin"]["Chat"], new() { [InputParameterName] = prompt });

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

        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._testOutputHelper);
        this._kernelBuilder
            .AddOpenAITextGeneration(
                serviceId: openAIConfiguration.ServiceId,
                modelId: openAIConfiguration.ModelId,
                apiKey: "INVALID_KEY"); // Use an invalid API key to force a 401 Unauthorized response
        this._kernelBuilder.Services.ConfigureHttpClientDefaults(c =>
        {
            // Use a standard resiliency policy, augmented to retry on 401 Unauthorized for this example
            c.AddStandardResilienceHandler().Configure(o =>
            {
                o.Retry.ShouldHandle = args => ValueTask.FromResult(args.Outcome.Result?.StatusCode is HttpStatusCode.Unauthorized);
            });
        });
        Kernel target = this._kernelBuilder.Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");

        // Act
        await Assert.ThrowsAsync<HttpOperationException>(() => target.InvokeAsync(plugins["SummarizePlugin"]["Summarize"], new() { [InputParameterName] = prompt }));

        // Assert
        Assert.Contains(expectedOutput, this._testOutputHelper.GetLogs(), StringComparison.OrdinalIgnoreCase);
    }

    // If the test fails, please note that SK retry logic may not be fully integrated into the underlying code using Azure SDK
    [Theory]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Resilience event occurred")]
    public async Task AzureOpenAIHttpRetryPolicyTestAsync(string prompt, string expectedOutput)
    {
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._testOutputHelper);
        IKernelBuilder builder = this._kernelBuilder;

        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        // Use an invalid API key to force a 401 Unauthorized response
        builder.AddAzureOpenAITextGeneration(
            deploymentName: azureOpenAIConfiguration.DeploymentName,
            modelId: azureOpenAIConfiguration.ModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: "INVALID_KEY");

        builder.Services.ConfigureHttpClientDefaults(c =>
        {
            // Use a standard resiliency policy, augmented to retry on 401 Unauthorized for this example
            c.AddStandardResilienceHandler().Configure(o =>
            {
                o.Retry.ShouldHandle = args => ValueTask.FromResult(args.Outcome.Result?.StatusCode is HttpStatusCode.Unauthorized);
            });
        });

        Kernel target = builder.Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");

        // Act
        await Assert.ThrowsAsync<HttpOperationException>(() => target.InvokeAsync(plugins["SummarizePlugin"]["Summarize"], new() { [InputParameterName] = prompt }));

        // Assert
        Assert.Contains(expectedOutput, this._testOutputHelper.GetLogs(), StringComparison.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task AzureOpenAIShouldReturnMetadataAsync(bool useChatModel)
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);

        if (useChatModel)
        {
            this.ConfigureAzureOpenAIChatAsText(this._kernelBuilder);
        }
        else
        {
            this.ConfigureAzureOpenAI(this._kernelBuilder);
        }

        var kernel = this._kernelBuilder.Build();

        var plugin = TestHelpers.ImportSamplePlugins(kernel, "FunPlugin");

        // Act
        var result = await kernel.InvokeAsync(plugin["FunPlugin"]["Limerick"]);

        // Assert
        Assert.NotNull(result.Metadata);

        // Usage
        Assert.True(result.Metadata.TryGetValue("Usage", out object? usageObject));
        Assert.NotNull(usageObject);

        var jsonObject = JsonSerializer.SerializeToElement(usageObject);
        Assert.True(jsonObject.TryGetProperty("PromptTokens", out JsonElement promptTokensJson));
        Assert.True(promptTokensJson.TryGetInt32(out int promptTokens));
        Assert.NotEqual(0, promptTokens);

        Assert.True(jsonObject.TryGetProperty("CompletionTokens", out JsonElement completionTokensJson));
        Assert.True(completionTokensJson.TryGetInt32(out int completionTokens));
        Assert.NotEqual(0, completionTokens);

        // ContentFilterResults
        Assert.True(result.Metadata.ContainsKey("ContentFilterResults"));
    }

    [Fact]
    public async Task OpenAIHttpInvalidKeyShouldReturnErrorDetailAsync()
    {
        // Arrange
        OpenAIConfiguration? openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();
        Assert.NotNull(openAIConfiguration);

        // Use an invalid API key to force a 401 Unauthorized response
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        Kernel target = this._kernelBuilder
            .AddOpenAITextGeneration(
                modelId: openAIConfiguration.ModelId,
                apiKey: "INVALID_KEY",
                serviceId: openAIConfiguration.ServiceId)
            .Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");

        // Act and Assert
        var ex = await Assert.ThrowsAsync<HttpOperationException>(() => target.InvokeAsync(plugins["SummarizePlugin"]["Summarize"], new() { [InputParameterName] = "Any" }));

        Assert.Equal(HttpStatusCode.Unauthorized, ((HttpOperationException)ex).StatusCode);
    }

    [Fact]
    public async Task AzureOpenAIHttpInvalidKeyShouldReturnErrorDetailAsync()
    {
        // Arrange
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._testOutputHelper);
        Kernel target = this._kernelBuilder
            .AddAzureOpenAITextGeneration(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                modelId: azureOpenAIConfiguration.ModelId,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: "INVALID_KEY",
                serviceId: azureOpenAIConfiguration.ServiceId)
            .Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");

        // Act and Assert
        var ex = await Assert.ThrowsAsync<HttpOperationException>(() => target.InvokeAsync(plugins["SummarizePlugin"]["Summarize"], new() { [InputParameterName] = "Any" }));

        Assert.Equal(HttpStatusCode.Unauthorized, ((HttpOperationException)ex).StatusCode);
    }

    [Fact]
    public async Task AzureOpenAIHttpExceededMaxTokensShouldReturnErrorDetailAsync()
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);

        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._testOutputHelper);
        Kernel target = this._kernelBuilder
            .AddAzureOpenAITextGeneration(
                deploymentName: azureOpenAIConfiguration.DeploymentName,
                modelId: azureOpenAIConfiguration.ModelId,
                endpoint: azureOpenAIConfiguration.Endpoint,
                apiKey: azureOpenAIConfiguration.ApiKey,
                serviceId: azureOpenAIConfiguration.ServiceId)
            .Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");

        // Act
        // Assert
        await Assert.ThrowsAsync<HttpOperationException>(() => plugins["SummarizePlugin"]["Summarize"].InvokeAsync(target, new() { [InputParameterName] = string.Join('.', Enumerable.Range(1, 40000)) }));
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
            $$"""Input:{{lineEnding}}{"name": "John", "age": 30}{{lineEnding}}{{lineEnding}}Request:{{lineEnding}}name""";

        const string ExpectedAnswerContains = "<result>John</result>";

        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        Kernel target = this._kernelBuilder.Build();

        this._serviceConfiguration[service](target);

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "ChatPlugin");

        // Act
        FunctionResult actual = await target.InvokeAsync(plugins["ChatPlugin"]["Chat"], new() { [InputParameterName] = prompt });

        // Assert
        Assert.Contains(ExpectedAnswerContains, actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task AzureOpenAIInvokePromptTestAsync()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;
        this.ConfigureAzureOpenAI(builder);
        Kernel target = builder.Build();

        var prompt = "Where is the most famous fish market in Seattle, Washington, USA?";

        // Act
        FunctionResult actual = await target.InvokePromptAsync(prompt, new(new OpenAIPromptExecutionSettings() { MaxTokens = 150 }));

        // Assert
        Assert.Contains("Pike Place", actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
        Assert.NotNull(actual.Metadata);
    }

    [Fact]
    public async Task AzureOpenAIInvokePromptWithMultipleResultsTestAsync()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;
        this.ConfigureAzureOpenAIChatAsText(builder);
        Kernel target = builder.Build();

        var prompt = "Where is the most famous fish market in Seattle, Washington, USA?";

        var executionSettings = new OpenAIPromptExecutionSettings() { MaxTokens = 150, ResultsPerPrompt = 3 };

        // Act
        FunctionResult actual = await target.InvokePromptAsync(prompt, new(executionSettings));

        // Assert
        Assert.Null(actual.Metadata);

        var chatMessageContents = actual.GetValue<IReadOnlyList<ChatMessageContent>>();

        Assert.NotNull(chatMessageContents);
        Assert.Equal(executionSettings.ResultsPerPrompt, chatMessageContents.Count);

        foreach (var chatMessageContent in chatMessageContents)
        {
            Assert.NotNull(chatMessageContent.Metadata);
            Assert.Contains("Pike Place", chatMessageContent.Content, StringComparison.OrdinalIgnoreCase);
        }
    }

    [Fact]
    public async Task AzureOpenAIDefaultValueTestAsync()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;
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
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;
        this.ConfigureAzureOpenAI(builder);
        this.ConfigureInvalidAzureOpenAI(builder);

        Kernel target = builder.Build();

        var prompt = "Where is the most famous fish market in Seattle, Washington, USA?";
        var defaultPromptModel = new PromptTemplateConfig(prompt) { Name = "FishMarket1" };
        var azurePromptModel = PromptTemplateConfig.FromJson("""
            {
                "name": "FishMarket2",
                "execution_settings": {
                    "azure-gpt-35-turbo-instruct": {
                        "max_tokens": 256
                    }
                }
            }
            """);
        azurePromptModel.Template = prompt;

        var defaultFunc = target.CreateFunctionFromPrompt(defaultPromptModel);
        var azureFunc = target.CreateFunctionFromPrompt(azurePromptModel);

        // Act
        await Assert.ThrowsAsync<HttpOperationException>(() => target.InvokeAsync(defaultFunc));

        FunctionResult azureResult = await target.InvokeAsync(azureFunc);

        // Assert
        Assert.Contains("Pike Place", azureResult.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ChatSystemPromptIsNotIgnoredAsync()
    {
        // Arrange
        var settings = new OpenAIPromptExecutionSettings { ChatSystemPrompt = "Reply \"I don't know\" to every question." };

        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;
        this.ConfigureAzureOpenAIChatAsText(builder);
        Kernel target = builder.Build();

        // Act
        var result = await target.InvokePromptAsync("Where is the most famous fish market in Seattle, Washington, USA?", new(settings));

        // Assert
        Assert.Contains("I don't know", result.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task SemanticKernelVersionHeaderIsSentAsync()
    {
        // Arrange
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.ChatDeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.ApiKey);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);
        Assert.NotNull(azureOpenAIConfiguration.ServiceId);

        using var defaultHandler = new HttpClientHandler();
        using var httpHeaderHandler = new HttpHeaderHandler(defaultHandler);
        using var httpClient = new HttpClient(httpHeaderHandler);
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;
        builder.AddAzureOpenAIChatCompletion(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName,
            modelId: azureOpenAIConfiguration.ChatModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey,
            serviceId: azureOpenAIConfiguration.ServiceId,
            httpClient: httpClient);
        Kernel target = builder.Build();

        // Act
        var result = await target.InvokePromptAsync("Where is the most famous fish market in Seattle, Washington, USA?");

        // Assert
        Assert.NotNull(httpHeaderHandler.RequestHeaders);
        Assert.True(httpHeaderHandler.RequestHeaders.TryGetValues("Semantic-Kernel-Version", out var values));
    }

    [Theory(Skip = "This test is for manual verification.")]
    [InlineData(null, null)]
    [InlineData(false, null)]
    [InlineData(true, 2)]
    [InlineData(true, 5)]
    public async Task LogProbsDataIsReturnedWhenRequestedAsync(bool? logprobs, int? topLogprobs)
    {
        // Arrange
        var settings = new OpenAIPromptExecutionSettings { Logprobs = logprobs, TopLogprobs = topLogprobs };

        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;
        this.ConfigureAzureOpenAIChatAsText(builder);
        Kernel target = builder.Build();

        // Act
        var result = await target.InvokePromptAsync("Hi, can you help me today?", new(settings));

        var logProbabilityInfo = result.Metadata?["LogProbabilityInfo"] as ChatChoiceLogProbabilityInfo;

        // Assert
        if (logprobs is true)
        {
            Assert.NotNull(logProbabilityInfo);
            Assert.Equal(topLogprobs, logProbabilityInfo.TokenLogProbabilityResults[0].TopLogProbabilityEntries.Count);
        }
        else
        {
            Assert.Null(logProbabilityInfo);
        }
    }

    #region internals

    private readonly XunitLogger<Kernel> _logger = new(output);
    private readonly RedirectOutput _testOutputHelper = new(output);

    private readonly Dictionary<AIServiceType, Action<Kernel>> _serviceConfiguration = [];

    public void Dispose()
    {
        this._logger.Dispose();
        this._testOutputHelper.Dispose();
    }

    private void ConfigureChatOpenAI(IKernelBuilder kernelBuilder)
    {
        var openAIConfiguration = this._configuration.GetSection("OpenAI").Get<OpenAIConfiguration>();

        Assert.NotNull(openAIConfiguration);
        Assert.NotNull(openAIConfiguration.ChatModelId);
        Assert.NotNull(openAIConfiguration.ApiKey);
        Assert.NotNull(openAIConfiguration.ServiceId);

        kernelBuilder.AddOpenAIChatCompletion(
            modelId: openAIConfiguration.ChatModelId,
            apiKey: openAIConfiguration.ApiKey,
            serviceId: openAIConfiguration.ServiceId);
    }

    private void ConfigureAzureOpenAI(IKernelBuilder kernelBuilder)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.DeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);
        Assert.NotNull(azureOpenAIConfiguration.ApiKey);
        Assert.NotNull(azureOpenAIConfiguration.ServiceId);

        kernelBuilder.AddAzureOpenAITextGeneration(
            deploymentName: azureOpenAIConfiguration.DeploymentName,
            modelId: azureOpenAIConfiguration.ModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey,
            serviceId: azureOpenAIConfiguration.ServiceId);
    }
    private void ConfigureInvalidAzureOpenAI(IKernelBuilder kernelBuilder)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.DeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);

        kernelBuilder.AddAzureOpenAITextGeneration(
            deploymentName: azureOpenAIConfiguration.DeploymentName,
            modelId: azureOpenAIConfiguration.ModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: "invalid-api-key",
            serviceId: $"invalid-{azureOpenAIConfiguration.ServiceId}");
    }

    private void ConfigureAzureOpenAIChatAsText(IKernelBuilder kernelBuilder)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.ChatDeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.ApiKey);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);
        Assert.NotNull(azureOpenAIConfiguration.ServiceId);

        kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName,
            modelId: azureOpenAIConfiguration.ChatModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey,
            serviceId: azureOpenAIConfiguration.ServiceId);
    }

    private sealed class HttpHeaderHandler(HttpMessageHandler innerHandler) : DelegatingHandler(innerHandler)
    {
        public System.Net.Http.Headers.HttpRequestHeaders? RequestHeaders { get; private set; }

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            this.RequestHeaders = request.Headers;
            return await base.SendAsync(request, cancellationToken);
        }
    }

    #endregion
}
