// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using SemanticKernel.IntegrationTests.TestSettings;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Ollama;

#pragma warning disable xUnit1004 // Contains test methods used in manual verification. Disable warning for this file only.

public sealed class OllamaCompletionTests(ITestOutputHelper output) : IDisposable
{
    private const string InputParameterName = "input";
    private readonly IKernelBuilder _kernelBuilder = Kernel.CreateBuilder();
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OllamaCompletionTests>()
        .Build();

    [Theory(Skip = "For manual verification only")]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    public async Task ItStreamingTestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;

        this.ConfigureChatOllama(this._kernelBuilder);

        Kernel target = builder.Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "ChatPlugin");

        StringBuilder fullResult = new();
        // Act
        await foreach (var content in target.InvokeStreamingAsync<StreamingKernelContent>(plugins["ChatPlugin"]["Chat"], new() { [InputParameterName] = prompt }))
        {
            if (content is StreamingChatMessageContent messageContent)
            {
                Assert.NotNull(messageContent.Role);
            }

            fullResult.Append(content);
        }

        // Assert
        Assert.Contains(expectedAnswerContains, fullResult.ToString(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task ItShouldReturnMetadataAsync()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);

        this.ConfigureChatOllama(this._kernelBuilder);

        var kernel = this._kernelBuilder.Build();

        var plugin = TestHelpers.ImportSamplePlugins(kernel, "FunPlugin");

        // Act
        StreamingKernelContent? lastUpdate = null;
        await foreach (var update in kernel.InvokeStreamingAsync(plugin["FunPlugin"]["Limerick"]))
        {
            lastUpdate = update;
        }

        // Assert
        Assert.NotNull(lastUpdate);
        Assert.NotNull(lastUpdate.Metadata);

        // CreatedAt
        Assert.True(lastUpdate.Metadata.TryGetValue("CreatedAt", out object? createdAt));
    }

    [Theory(Skip = "For manual verification only")]
    [InlineData("\n")]
    [InlineData("\r\n")]
    public async Task ItCompletesWithDifferentLineEndingsAsync(string lineEnding)
    {
        // Arrange
        var prompt =
            "Given a json input and a request. Apply the request on the json input and return the result. " +
            $"Put the result in between <result></result> tags{lineEnding}" +
            $$"""Input:{{lineEnding}}{"name": "John", "age": 30}{{lineEnding}}{{lineEnding}}Request:{{lineEnding}}name""";

        const string ExpectedAnswerContains = "result";

        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        this.ConfigureChatOllama(this._kernelBuilder);

        Kernel target = this._kernelBuilder.Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "ChatPlugin");

        // Act
        FunctionResult actual = await target.InvokeAsync(plugins["ChatPlugin"]["Chat"], new() { [InputParameterName] = prompt });

        // Assert
        Assert.Contains(ExpectedAnswerContains, actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task ItInvokePromptTestAsync()
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;
        this.ConfigureChatOllama(builder);
        Kernel target = builder.Build();

        var prompt = "Where is the most famous fish market in Seattle, Washington, USA?";

        // Act
        FunctionResult actual = await target.InvokePromptAsync(prompt, new(new OllamaPromptExecutionSettings() { Temperature = 0.5f }));

        // Assert
        Assert.Contains("Pike Place", actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Theory(Skip = "For manual verification only")]
    [InlineData("Where is the most famous fish market in Seattle, Washington, USA?", "Pike Place")]
    public async Task ItInvokeTestAsync(string prompt, string expectedAnswerContains)
    {
        // Arrange
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;

        this.ConfigureChatOllama(this._kernelBuilder);

        Kernel target = builder.Build();

        IReadOnlyKernelPluginCollection plugins = TestHelpers.ImportSamplePlugins(target, "ChatPlugin");

        // Act
        FunctionResult actual = await target.InvokeAsync(plugins["ChatPlugin"]["Chat"], new() { [InputParameterName] = prompt });

        // Assert
        Assert.Contains(expectedAnswerContains, actual.GetValue<string>(), StringComparison.OrdinalIgnoreCase);
    }

    [Fact(Skip = "For manual verification only")]
    public async Task ItShouldHaveSemanticKernelVersionHeaderAsync()
    {
        // Arrange
        var config = this._configuration.GetSection("Ollama").Get<OllamaConfiguration>();
        Assert.NotNull(config);
        Assert.NotNull(config.ModelId);
        Assert.NotNull(config.Endpoint);

        using var defaultHandler = new HttpClientHandler();
        using var httpHeaderHandler = new HttpHeaderHandler(defaultHandler);
        using var httpClient = new HttpClient(httpHeaderHandler);
        this._kernelBuilder.Services.AddSingleton<ILoggerFactory>(this._logger);
        var builder = this._kernelBuilder;
        builder.AddOllamaChatCompletion(
            endpoint: config.Endpoint,
            modelId: config.ModelId,
            httpClient: httpClient);
        Kernel target = builder.Build();

        // Act
        var result = await target.InvokePromptAsync("Where is the most famous fish market in Seattle, Washington, USA?");

        // Assert
        Assert.NotNull(httpHeaderHandler.RequestHeaders);
        Assert.True(httpHeaderHandler.RequestHeaders.TryGetValues("Semantic-Kernel-Version", out var values));
    }

    #region internals

    private readonly XunitLogger<Kernel> _logger = new(output);
    private readonly RedirectOutput _testOutputHelper = new(output);

    public void Dispose()
    {
        this._logger.Dispose();
        this._testOutputHelper.Dispose();
    }

    private void ConfigureChatOllama(IKernelBuilder kernelBuilder)
    {
        var config = this._configuration.GetSection("Ollama").Get<OllamaConfiguration>();

        Assert.NotNull(config);
        Assert.NotNull(config.Endpoint);
        Assert.NotNull(config.ModelId);

        kernelBuilder.AddOllamaChatCompletion(
            modelId: config.ModelId,
            endpoint: config.Endpoint);
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
