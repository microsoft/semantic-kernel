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

public abstract class TestsBase
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddUserSecrets<TestsBase>()
        .AddEnvironmentVariables()
        .Build();

    protected ITestOutputHelper Output { get; }

    private readonly string _huggingFaceApiKey;
    private readonly string _huggingFaceChatCompletionModel;
    private readonly string _huggingFaceTextGenerationModel;
    private readonly string _huggingFaceEmbeddingModel;
    private readonly Uri _huggingFaceRemoteEndpoint;
    private readonly Uri _huggingFaceRemoteChatCompletionDeploymentEndpoint;

    protected TestsBase(ITestOutputHelper output)
    {
        this.Output = output;

        this._huggingFaceApiKey = this._configuration.GetSection("HuggingFace:ApiKey").Get<string>()!;
        this._huggingFaceChatCompletionModel = this._configuration.GetSection("HuggingFace:ChatCompletionModelId").Get<string>()!;
        this._huggingFaceTextGenerationModel = this._configuration.GetSection("HuggingFace:TextGenerationModelId").Get<string>()!;
        this._huggingFaceEmbeddingModel = this._configuration.GetSection("HuggingFace:EmbeddingModelId").Get<string>()!;
        this._huggingFaceRemoteEndpoint = new Uri(this._configuration.GetSection("HuggingFace:Endpoint").Get<string>()!);
        this._huggingFaceRemoteChatCompletionDeploymentEndpoint = new Uri(this._configuration.GetSection("HuggingFace:ChatCompletionDeploymentEndpoint").Get<string>()!);
    }

    protected IChatCompletionService RemoteChatCompletionService =>
        new HuggingFaceChatCompletionService(
            model: this._huggingFaceChatCompletionModel,
            endpoint: this._huggingFaceRemoteChatCompletionDeploymentEndpoint,
            apiKey: this._huggingFaceApiKey);

    protected ITextGenerationService GetLocalTextGenerationService(Uri endpoint) =>
        new HuggingFaceTextGenerationService(
            model: this._huggingFaceTextGenerationModel,
            endpoint: endpoint,
            apiKey: this._huggingFaceApiKey);

    protected ITextGenerationService RemoteTextGenerationService =>
        new HuggingFaceTextGenerationService(
            model: this._huggingFaceTextGenerationModel,
            endpoint: this._huggingFaceRemoteEndpoint,
            apiKey: this._huggingFaceApiKey);

    protected ITextGenerationService GetRemoteTextGenerationServiceWithCustomHttpClient(HttpClient httpClient) =>
        new HuggingFaceTextGenerationService(
            model: this._huggingFaceTextGenerationModel,
            endpoint: this._huggingFaceRemoteEndpoint,
            apiKey: this._huggingFaceApiKey,
            httpClient: httpClient);

    protected ITextEmbeddingGenerationService RemoteTextEmbeddingService =>
        new HuggingFaceTextEmbeddingGenerationService(
            model: this._huggingFaceEmbeddingModel,
            endpoint: this._huggingFaceRemoteEndpoint,
            apiKey: this._huggingFaceApiKey);

    protected Kernel BuildKernelWithRemoteChatCompletionService() =>
        Kernel.CreateBuilder()
        .AddHuggingFaceChatCompletion(
            model: this._huggingFaceChatCompletionModel,
            endpoint: this._huggingFaceRemoteChatCompletionDeploymentEndpoint,
            apiKey: this._huggingFaceApiKey)
        .Build();
}
