// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Http.Resilience;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureOpenAI;
using OpenAI.Chat;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureOpenAI;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class AzureOpenAIChatCompletionTests : BaseIntegrationTest
{
    [Fact]
    //[Fact(Skip = "Skipping while we investigate issue with GitHub actions.")]
    public async Task ItCanUseAzureOpenAiChatForTextGenerationAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var func = kernel.CreateFunctionFromPrompt(
            "List the two planets after '{{$input}}', excluding moons, using bullet points.",
            new AzureOpenAIPromptExecutionSettings());

        // Act
        var result = await func.InvokeAsync(kernel, new() { [InputParameterName] = "Jupiter" });

        // Assert
        Assert.NotNull(result);
        Assert.Contains("Saturn", result.GetValue<string>(), StringComparison.InvariantCultureIgnoreCase);
        Assert.Contains("Uranus", result.GetValue<string>(), StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact]
    public async Task AzureOpenAIStreamingTestAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var plugins = TestHelpers.ImportSamplePlugins(kernel, "ChatPlugin");

        StringBuilder fullResult = new();

        var prompt = "Where is the most famous fish market in Seattle, Washington, USA?";

        // Act
        await foreach (var content in kernel.InvokeStreamingAsync<StreamingKernelContent>(plugins["ChatPlugin"]["Chat"], new() { [InputParameterName] = prompt }))
        {
            fullResult.Append(content);
        }

        // Assert
        Assert.Contains("Pike Place", fullResult.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task AzureOpenAIHttpRetryPolicyTestAsync()
    {
        // Arrange
        List<HttpStatusCode?> statusCodes = [];

        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();

        var kernelBuilder = Kernel.CreateBuilder();

        kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: azureOpenAIConfiguration!.ChatDeploymentName!,
            modelId: azureOpenAIConfiguration.ChatModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: "INVALID_KEY");

        kernelBuilder.Services.ConfigureHttpClientDefaults(c =>
        {
            // Use a standard resiliency policy, augmented to retry on 401 Unauthorized for this example
            c.AddStandardResilienceHandler().Configure(o =>
            {
                o.Retry.ShouldHandle = args => ValueTask.FromResult(args.Outcome.Result?.StatusCode is HttpStatusCode.Unauthorized);
                o.Retry.OnRetry = args =>
                {
                    statusCodes.Add(args.Outcome.Result?.StatusCode);
                    return ValueTask.CompletedTask;
                };
            });
        });

        var target = kernelBuilder.Build();

        var plugins = TestHelpers.ImportSamplePlugins(target, "SummarizePlugin");

        var prompt = "Where is the most famous fish market in Seattle, Washington, USA?";

        // Act
        var exception = await Assert.ThrowsAsync<HttpOperationException>(() => target.InvokeAsync(plugins["SummarizePlugin"]["Summarize"], new() { [InputParameterName] = prompt }));

        // Assert
        Assert.All(statusCodes, s => Assert.Equal(HttpStatusCode.Unauthorized, s));
        Assert.Equal(HttpStatusCode.Unauthorized, ((HttpOperationException)exception).StatusCode);
    }

    [Fact]
    public async Task AzureOpenAIShouldReturnMetadataAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var plugins = TestHelpers.ImportSamplePlugins(kernel, "FunPlugin");

        // Act
        var result = await kernel.InvokeAsync(plugins["FunPlugin"]["Limerick"]);

        // Assert
        Assert.NotNull(result.Metadata);

        // Usage
        Assert.True(result.Metadata.TryGetValue("Usage", out object? usageObject));
        Assert.NotNull(usageObject);

        var jsonObject = JsonSerializer.SerializeToElement(usageObject);
        Assert.True(jsonObject.TryGetProperty("InputTokens", out JsonElement promptTokensJson));
        Assert.True(promptTokensJson.TryGetInt32(out int promptTokens));
        Assert.NotEqual(0, promptTokens);

        Assert.True(jsonObject.TryGetProperty("OutputTokens", out JsonElement completionTokensJson));
        Assert.True(jsonObject.TryGetProperty("InputTokenCount", out JsonElement promptTokensJson));
        Assert.True(promptTokensJson.TryGetInt32(out int promptTokens));
        Assert.NotEqual(0, promptTokens);

        Assert.True(jsonObject.TryGetProperty("OutputTokenCount", out JsonElement completionTokensJson));
        Assert.True(jsonObject.TryGetProperty("InputTokenCount", out JsonElement promptTokensJson));
        Assert.True(promptTokensJson.TryGetInt32(out int promptTokens));
        Assert.NotEqual(0, promptTokens);

        Assert.True(jsonObject.TryGetProperty("OutputTokenCount", out JsonElement completionTokensJson));
        Assert.True(completionTokensJson.TryGetInt32(out int completionTokens));
        Assert.NotEqual(0, completionTokens);
    }

    [Theory(Skip = "This test is for manual verification.")]
    [InlineData("\n")]
    [InlineData("\r\n")]
    public async Task CompletionWithDifferentLineEndingsAsync(string lineEnding)
    {
        // Arrange
        var prompt =
            "Given a json input and a request. Apply the request on the json input and return the result. " +
            $"Put the result in between <result></result> tags{lineEnding}" +
            $$"""Input:{{lineEnding}}{"name": "John", "age": 30}{{lineEnding}}{{lineEnding}}Request:{{lineEnding}}name""";

        var kernel = this.CreateAndInitializeKernel();

        var plugins = TestHelpers.ImportSamplePlugins(kernel, "ChatPlugin");

        // Act
        FunctionResult actual = await kernel.InvokeAsync(plugins["ChatPlugin"]["Chat"], new() { [InputParameterName] = prompt });

        // Assert
        Assert.Contains("<result>John</result>", actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task ChatSystemPromptIsNotIgnoredAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var settings = new AzureOpenAIPromptExecutionSettings { ChatSystemPrompt = "Reply \"I don't know\" to every question." };

        // Act
        var result = await kernel.InvokePromptAsync("Where is the most famous fish market in Seattle, Washington, USA?", new(settings));

        // Assert
        Assert.Contains("I don't know", result.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task SemanticKernelVersionHeaderIsSentAsync()
    {
        // Arrange
        using var defaultHandler = new HttpClientHandler();
        using var httpHeaderHandler = new HttpHeaderHandler(defaultHandler);
        using var httpClient = new HttpClient(httpHeaderHandler);

        var kernel = this.CreateAndInitializeKernel(httpClient);

        // Act
        var result = await kernel.InvokePromptAsync("Where is the most famous fish market in Seattle, Washington, USA?");

        // Assert
        Assert.NotNull(httpHeaderHandler.RequestHeaders);
        Assert.True(httpHeaderHandler.RequestHeaders.TryGetValues("Semantic-Kernel-Version", out var values));
    }

    //[Theory(Skip = "This test is for manual verification.")]
    [Theory]
    [InlineData(null, null)]
    [InlineData(false, null)]
    [InlineData(true, 2)]
    [InlineData(true, 5)]
    public async Task LogProbsDataIsReturnedWhenRequestedAsync(bool? logprobs, int? topLogprobs)
    {
        // Arrange
        var settings = new AzureOpenAIPromptExecutionSettings { Logprobs = logprobs, TopLogprobs = topLogprobs };

        var kernel = this.CreateAndInitializeKernel();

        // Act
        var result = await kernel.InvokePromptAsync("Hi, can you help me today?", new(settings));

        var logProbabilityInfo = result.Metadata?["ContentTokenLogProbabilities"] as IReadOnlyList<ChatTokenLogProbabilityInfo>;
        var logProbabilityInfo = result.Metadata?["ContentTokenLogProbabilities"] as IReadOnlyList<ChatTokenLogProbabilityInfo>;
        var logProbabilityInfo = result.Metadata?["ContentTokenLogProbabilities"] as IReadOnlyList<ChatTokenLogProbabilityDetails>;
        var logProbabilityInfo = result.Metadata?["ContentTokenLogProbabilities"] as IReadOnlyList<ChatTokenLogProbabilityDetails>;
        var logProbabilityInfo = result.Metadata?["ContentTokenLogProbabilities"] as IReadOnlyList<ChatTokenLogProbabilityDetails>;
        var logProbabilityInfo = result.Metadata?["ContentTokenLogProbabilities"] as IReadOnlyList<ChatTokenLogProbabilityDetails>;

        // Assert
        Assert.NotNull(logProbabilityInfo);

        if (logprobs is true)
        {
            Assert.NotNull(logProbabilityInfo);
            Assert.Equal(topLogprobs, logProbabilityInfo[0].TopLogProbabilities.Count);
        }
        else
        {
            Assert.Empty(logProbabilityInfo);
        }
    }

    #region internals

    private Kernel CreateAndInitializeKernel(HttpClient? httpClient = null)
    {
        var azureOpenAIConfiguration = this._configuration.GetSection("AzureOpenAI").Get<AzureOpenAIConfiguration>();
        Assert.NotNull(azureOpenAIConfiguration);
        Assert.NotNull(azureOpenAIConfiguration.ChatDeploymentName);
        Assert.NotNull(azureOpenAIConfiguration.ApiKey);
        Assert.NotNull(azureOpenAIConfiguration.Endpoint);
        Assert.NotNull(azureOpenAIConfiguration.ServiceId);

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddAzureOpenAIChatCompletion(
            deploymentName: azureOpenAIConfiguration.ChatDeploymentName,
            modelId: azureOpenAIConfiguration.ChatModelId,
            endpoint: azureOpenAIConfiguration.Endpoint,
            apiKey: azureOpenAIConfiguration.ApiKey,
            credentials: new AzureCliCredential(),
            serviceId: azureOpenAIConfiguration.ServiceId,
            httpClient: httpClient);

        return kernelBuilder.Build();
    }

    private const string InputParameterName = "input";

    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureOpenAIChatCompletionStreamingTests>()
        .Build();

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
