// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Anthropic;

public abstract class TestsBase(ITestOutputHelper output)
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddUserSecrets<TestsBase>()
        .AddEnvironmentVariables()
        .Build();

    protected ITestOutputHelper Output { get; } = output;

    protected IChatCompletionService GetChatService(ServiceType serviceType) => serviceType switch
    {
        ServiceType.Anthropic => new AnthropicChatCompletionService(
            modelId: this.AnthropicGetModel(),
            apiKey: this.AnthropicGetApiKey()),
        ServiceType.VertexAI => throw new NotImplementedException("Implement in next PR"), // TODO: Implement in next PR
        _ => throw new ArgumentOutOfRangeException(nameof(serviceType), serviceType, null)
    };

    public enum ServiceType
    {
        Anthropic,
        VertexAI
    }

    private string AnthropicGetModel() => this._configuration.GetSection("Anthropic:ModelId").Get<string>()!;
    private string AnthropicGetApiKey() => this._configuration.GetSection("Anthropic:ApiKey").Get<string>()!;
    private string VertexAIGetModel() => this._configuration.GetSection("VertexAI:Anthropic:ModelId").Get<string>()!;
    private string VertexAIGetEndpoint() => this._configuration.GetSection("VertexAI:Anthropic:Endpoint").Get<string>()!;
    private string VertexAIGetBearerKey() => this._configuration.GetSection("VertexAI:BearerKey").Get<string>()!;
}
