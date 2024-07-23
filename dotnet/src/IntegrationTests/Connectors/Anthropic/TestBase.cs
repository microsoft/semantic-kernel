// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Anthropic;

public abstract class TestBase(ITestOutputHelper output)
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddUserSecrets<TestBase>()
        .AddEnvironmentVariables()
        .Build();

    protected ITestOutputHelper Output { get; } = output;

    protected IChatCompletionService GetChatService(ServiceType serviceType) => serviceType switch
    {
        ServiceType.Anthropic => new AnthropicChatCompletionService(
            new AnthropicClientOptions
            {
                ModelId = this.AnthropicGetModel(),
                ApiKey = this.AnthropicGetApiKey()
            }),

        ServiceType.VertexAI => new AnthropicChatCompletionService(
            new VertexAIAnthropicClientOptions
            {
                ModelId = this.VertexAIGetModel(),
                Endpoint = new Uri(this.VertexAIGetEndpoint()),
                BearerKey = this.VertexAIGetBearerKey()
            }),

        ServiceType.AmazonBedrock => new AnthropicChatCompletionService(
            new AmazonBedrockAnthropicClientOptions
            {
                ModelId = this.AmazonBedrockGetModel(),
                Endpoint = new Uri(this.AmazonBedrockGetEndpoint()),
                BearerKey = this.AmazonBedrockGetBearerKey() // TODO: setup aws bedrock claude
            }),
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
    private string AmazonBedrockGetBearerKey() => this._configuration.GetSection("AmazonBedrock:Anthropic:BearerKey").Get<string>()!;
    private string AmazonBedrockGetModel() => this._configuration.GetSection("AmazonBedrock:Anthropic:ModelId").Get<string>()!;
    private string AmazonBedrockGetEndpoint() => this._configuration.GetSection("AmazonBedrock:Anthropic:Endpoint").Get<string>()!;
}
