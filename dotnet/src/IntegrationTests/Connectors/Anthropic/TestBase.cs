// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Anthropic;

public abstract class TestBase(ITestOutputHelper output)
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddUserSecrets<TestBase>()
        .AddEnvironmentVariables()
        .Build();

    protected ITestOutputHelper Output { get; } = output;

    protected IChatCompletionService GetChatService(ServiceType serviceType) => serviceType switch
    {
        ServiceType.Anthropic => new AnthropicChatCompletionService(
            modelId: this.AnthropicGetModel(),
            apiKey: this.AnthropicGetApiKey()),
        ServiceType.VertexAI => new AnthropicChatCompletionService(
            modelId: this.VertexAIGetModel(),
            endpoint: new Uri(this.VertexAIGetEndpoint()),
            options: new VertexAIAnthropicClientOptions(),
            requestHandler: requestMessage =>
            {
                requestMessage.Headers.Authorization = new("Bearer", this.VertexAIGetBearerKey());
                return ValueTask.CompletedTask;
            }),
        ServiceType.AmazonBedrock => new AnthropicChatCompletionService(
            modelId: this.AmazonBedrockGetModel(),
            endpoint: new Uri(this.AmazonBedrockGetEndpoint()),
            options: new AmazonBedrockAnthropicClientOptions(),
            requestHandler: _ => throw new NotImplementedException("setup later")), // TODO: setup aws bedrock claude
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
}
