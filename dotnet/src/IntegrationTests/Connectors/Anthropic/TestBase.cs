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
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddUserSecrets<TestBase>()
        .AddEnvironmentVariables()
        .Build();

    protected ITestOutputHelper Output { get; } = output;

    protected IChatCompletionService GetChatService(ServiceType serviceType) => serviceType switch
    {
        ServiceType.Anthropic => new AnthropicChatCompletionService(this.AnthropicGetModel(), this.AnthropicGetApiKey(), new()),
        ServiceType.VertexAI => new AnthropicChatCompletionService(this.VertexAIGetModel(), this.VertexAIGetBearerKey(), new VertexAIAnthropicClientOptions(), this.VertexAIGetEndpoint()),
        ServiceType.AmazonBedrock => new AnthropicChatCompletionService(this.VertexAIGetModel(), this.AmazonBedrockGetBearerKey(), new AmazonBedrockAnthropicClientOptions(), this.VertexAIGetEndpoint()),
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
    private Uri VertexAIGetEndpoint() => new(this._configuration.GetSection("VertexAI:Anthropic:Endpoint").Get<string>()!);
    private Func<ValueTask<string>> VertexAIGetBearerKey() => () => ValueTask.FromResult(this._configuration.GetSection("VertexAI:BearerKey").Get<string>()!);
    private Func<ValueTask<string>> AmazonBedrockGetBearerKey() => () => ValueTask.FromResult(this._configuration.GetSection("AmazonBedrock:Anthropic:BearerKey").Get<string>()!);
    private string AmazonBedrockGetModel() => this._configuration.GetSection("AmazonBedrock:Anthropic:ModelId").Get<string>()!;
    private Uri AmazonBedrockGetEndpoint() => new(this._configuration.GetSection("AmazonBedrock:Anthropic:Endpoint").Get<string>()!);
}
