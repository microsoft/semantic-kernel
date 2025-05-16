// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Azure;
using Azure.AI.Inference;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Http.Resilience;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureAIInference;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.AzureAIInference;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class AzureAIInferenceChatClientTests(ITestOutputHelper output) : BaseIntegrationTest, IDisposable
{
    private const string SkipReason = "For manual verification only";
    private const string InputParameterName = "input";
    private readonly XunitLogger<Kernel> _loggerFactory = new(output);
    private readonly RedirectOutput _testOutputHelper = new(output);
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<AzureAIInferenceChatClientTests>()
        .Build();

    [Theory(Skip = SkipReason)]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    public async Task InvokeGetResponseAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        var config = this._configuration.GetSection("AzureAIInference").Get<AzureAIInferenceConfiguration>();
        Assert.NotNull(config);

        IChatClient sut = this.CreateChatClient(config);

        List<ChatMessage> chatHistory = [new(Microsoft.Extensions.AI.ChatRole.User, prompt)];

        // Act
        var result = await sut.GetResponseAsync(chatHistory);

        // Assert
        Assert.NotNull(result);
        Assert.Contains(expectedAnswerContains, result.Text, StringComparison.OrdinalIgnoreCase);
    }

    [Theory(Skip = SkipReason)]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    public async Task InvokeGetStreamingResponseAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        var config = this._configuration.GetSection("AzureAIInference").Get<AzureAIInferenceConfiguration>();
        Assert.NotNull(config);

        IChatClient sut = this.CreateChatClient(config);

        List<ChatMessage> chatHistory = [new(Microsoft.Extensions.AI.ChatRole.User, prompt)];

        StringBuilder fullContent = new();

        // Act
        await foreach (var update in sut.GetStreamingResponseAsync(chatHistory))
        {
            fullContent.Append(update.Text);
        }

        // Assert
        Assert.Contains(expectedAnswerContains, fullContent.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanUseChatForTextGenerationAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var func = kernel.CreateFunctionFromPrompt(
            "List the two planets after '{{$input}}', excluding moons, using bullet points.",
            new AzureAIInferencePromptExecutionSettings());

        // Act
        var result = await func.InvokeAsync(kernel, new() { [InputParameterName] = "Jupiter" });

        // Assert
        Assert.NotNull(result);
        Assert.Contains("Saturn", result.GetValue<string>(), StringComparison.InvariantCultureIgnoreCase);
        Assert.Contains("Uranus", result.GetValue<string>(), StringComparison.InvariantCultureIgnoreCase);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItStreamingFromKernelTestAsync()
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

    [Fact(Skip = SkipReason)]
    public async Task ItHttpRetryPolicyTestAsync()
    {
        // Arrange
        List<HttpStatusCode?> statusCodes = [];

        var config = this._configuration.GetSection("AzureAIInference").Get<AzureAIInferenceConfiguration>();
        Assert.NotNull(config);
        Assert.NotNull(config.Endpoint);
        Assert.NotNull(config.ChatModelId);

        var kernelBuilder = Kernel.CreateBuilder();

        kernelBuilder.AddAzureAIInferenceChatClient(modelId: config.ChatModelId, endpoint: config.Endpoint, apiKey: "wrong");

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
        var exception = await Assert.ThrowsAsync<RequestFailedException>(() => target.InvokeAsync(plugins["SummarizePlugin"]["Summarize"], new() { [InputParameterName] = prompt }));

        // Assert
        Assert.All(statusCodes, s => Assert.Equal(HttpStatusCode.Unauthorized, s));
        Assert.Equal((int)HttpStatusCode.Unauthorized, ((RequestFailedException)exception).Status);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItShouldReturnInnerContentAsync()
    {
        // Arrange
        var kernel = this.CreateAndInitializeKernel();

        var plugins = TestHelpers.ImportSamplePlugins(kernel, "FunPlugin");

        // Act
        var result = await kernel.InvokeAsync(plugins["FunPlugin"]["Limerick"]);
        var content = result.GetValue<ChatMessageContent>();
        // Assert
        Assert.NotNull(content);
        Assert.NotNull(content.InnerContent);

        Assert.IsType<ChatCompletions>(content.InnerContent);
        var completions = (ChatCompletions)content.InnerContent;
        var usage = completions.Usage;

        // Usage
        Assert.NotEqual(0, usage.PromptTokens);
        Assert.NotEqual(0, usage.CompletionTokens);
    }

    [Theory(Skip = SkipReason)]
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

    private Kernel CreateAndInitializeKernel(HttpClient? httpClient = null)
    {
        var config = this._configuration.GetSection("AzureAIInference").Get<AzureAIInferenceConfiguration>();
        Assert.NotNull(config);
        Assert.NotNull(config.ApiKey);
        Assert.NotNull(config.Endpoint);
        Assert.NotNull(config.ChatModelId);

        var kernelBuilder = base.CreateKernelBuilder();

        kernelBuilder.AddAzureAIInferenceChatClient(
            config.ChatModelId,
            endpoint: config.Endpoint,
            apiKey: config.ApiKey,
            serviceId: config.ServiceId,
            httpClient: httpClient);

        return kernelBuilder.Build();
    }

    private IChatClient CreateChatClient(AzureAIInferenceConfiguration config)
    {
        var serviceCollection = new ServiceCollection();
        serviceCollection.AddSingleton(this._loggerFactory);

        Assert.NotNull(config.ChatModelId);

        if (config.ApiKey is not null)
        {
            serviceCollection.AddAzureAIInferenceChatClient(
                modelId: config.ChatModelId,
                endpoint: config.Endpoint,
                apiKey: config.ApiKey);
        }
        else
        {
            serviceCollection.AddAzureAIInferenceChatClient(
                modelId: config.ChatModelId,
                endpoint: config.Endpoint,
                credential: new AzureCliCredential());
        }

        var serviceProvider = serviceCollection.BuildServiceProvider();

        return serviceProvider.GetRequiredService<IChatClient>();
    }

    public void Dispose()
    {
        this._loggerFactory.Dispose();
        this._testOutputHelper.Dispose();
    }
}
