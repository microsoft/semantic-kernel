// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.HuggingFace;

public abstract class TestsBase(ITestOutputHelper output)

{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddUserSecrets<HuggingFace.TestsBase>()
        .AddEnvironmentVariables()
        .Build();

    protected ITestOutputHelper Output { get; } = output;

    protected IChatCompletionService GetRemoteChatCompletionService() =>
        new HuggingFaceChatCompletionService(
            model: this.HuggingFaceGetChatCompletionModel(),
            endpoint: this.HuggingFaceGetRemoteChatCompletionDeploymentEndpoint(),
            apiKey: this.HuggingFaceGetApiKey());

    protected ITextGenerationService GetLocalTextGenerationService(Uri endpoint) =>
        new HuggingFaceTextGenerationService(
            model: this.HuggingFaceGetTextGenerationModel(),
            endpoint: endpoint,
            apiKey: this.HuggingFaceGetApiKey());

    protected ITextGenerationService GetRemoteTextGenerationService() =>
        new HuggingFaceTextGenerationService(
            model: this.HuggingFaceGetTextGenerationModel(),
            endpoint: this.HuggingFaceGetRemoteEndpoint(),
            apiKey: this.HuggingFaceGetApiKey());

    protected ITextGenerationService GetRemoteTextGenerationServiceWithCustomHttpClient(HttpClient httpClient) =>
        new HuggingFaceTextGenerationService(
            model: this.HuggingFaceGetTextGenerationModel(),
            endpoint: this.HuggingFaceGetRemoteEndpoint(),
            apiKey: this.HuggingFaceGetApiKey(),
            httpClient: httpClient);

    protected ITextEmbeddingGenerationService GetRemoteTextEmbeddingService() =>
        new HuggingFaceTextEmbeddingGenerationService(
            model: this.HuggingFaceGetEmbeddingModel(),
            endpoint: this.HuggingFaceGetRemoteEndpoint(),
            apiKey: this.HuggingFaceGetApiKey());

    protected Kernel BuildKernelWithRemoteChatCompletionService() =>
        Kernel.CreateBuilder()
        .AddHuggingFaceChatCompletion(
            model: this.HuggingFaceGetChatCompletionModel(),
            endpoint: this.HuggingFaceGetRemoteChatCompletionDeploymentEndpoint(),
            apiKey: this.HuggingFaceGetApiKey())
        .Build();

    private string HuggingFaceGetApiKey() => this._configuration.GetSection("HuggingFace:ApiKey").Get<string>()!;
    private string HuggingFaceGetChatCompletionModel() => this._configuration.GetSection("HuggingFace:ChatCompletionModelId").Get<string>()!;
    private string HuggingFaceGetTextGenerationModel() => this._configuration.GetSection("HuggingFace:TextGenerationModelId").Get<string>()!;
    private string HuggingFaceGetEmbeddingModel() => this._configuration.GetSection("HuggingFace:EmbeddingModelId").Get<string>()!;
    private Uri HuggingFaceGetRemoteEndpoint() => new(this._configuration.GetSection("HuggingFace:Endpoint").Get<string>()!);
    private Uri HuggingFaceGetRemoteChatCompletionDeploymentEndpoint() => new(this._configuration.GetSection("HuggingFace:ChatCompletionDeploymentEndpoint").Get<string>()!);
}
