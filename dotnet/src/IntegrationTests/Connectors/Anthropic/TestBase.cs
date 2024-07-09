// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Anthropic;

public abstract class TestBase : IDisposable
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddUserSecrets<TestBase>()
        .AddEnvironmentVariables()
        .Build();

    private readonly HttpClient _vertexHttpClient;
    private readonly HttpClient _awsHttpClient;

    protected TestBase(ITestOutputHelper output)
    {
        this.Output = output;
        this._vertexHttpClient = new HttpClient { DefaultRequestHeaders = { { "Authorization", $"Bearer {this.VertexAIGetBearerKey()}" } } };
        this._awsHttpClient = new HttpClient(); // TODO: setup aws bedrock claude
    }

    protected ITestOutputHelper Output { get; }

    protected IChatCompletionService GetChatService(ServiceType serviceType) => serviceType switch
    {
        ServiceType.Anthropic => new AnthropicChatCompletionService(
            modelId: this.AnthropicGetModel(),
            apiKey: this.AnthropicGetApiKey()),
        ServiceType.VertexAI => new AnthropicChatCompletionService(
            modelId: this.VertexAIGetModel(),
            endpoint: new Uri(this.VertexAIGetEndpoint()),
            options: new VertexAIAnthropicClientOptions(),
            httpClient: this._vertexHttpClient),
        ServiceType.AmazonBedrock => new AnthropicChatCompletionService(
            modelId: this.AmazonBedrockGetModel(),
            endpoint: new Uri(this.AmazonBedrockGetEndpoint()),
            options: new AmazonBedrockAnthropicClientOptions(),
            httpClient: this._awsHttpClient), // TODO: setup aws bedrock claude
        _ => throw new ArgumentOutOfRangeException(nameof(serviceType), serviceType, null)
    };

    public enum ServiceType
    {
        Anthropic,
        VertexAI,
        AmazonBedrock
    }

    private string AnthropicGetModel() => this._configuration.GetSection("Anthropic:ModelId").Get<string>()!;
    private string AnthropicGetApiKey() => this._configuration.GetSection("Anthropic:ApiKey").Get<string>()!;
    private string VertexAIGetModel() => this._configuration.GetSection("VertexAI:Anthropic:ModelId").Get<string>()!;
    private string VertexAIGetEndpoint() => this._configuration.GetSection("VertexAI:Anthropic:Endpoint").Get<string>()!;
    private string VertexAIGetBearerKey() => this._configuration.GetSection("VertexAI:BearerKey").Get<string>()!;
    private string AmazonBedrockGetModel() => this._configuration.GetSection("AmazonBedrock:Anthropic:ModelId").Get<string>()!;
    private string AmazonBedrockGetEndpoint() => this._configuration.GetSection("AmazonBedrock:Anthropic:Endpoint").Get<string>()!;

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._vertexHttpClient.Dispose();
            this._awsHttpClient.Dispose();
        }
    }

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }
}
