// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.GoogleVertexAI;

public abstract class TestsBase
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .Build();

    protected ITestOutputHelper Output { get; }

    protected TestsBase(ITestOutputHelper output)
    {
        this.Output = output;
    }

    protected IChatCompletionService GetChatService(ServiceType serviceType) => serviceType switch
    {
        ServiceType.GoogleAI => new GoogleAIGeminiChatCompletionService(
            this.GoogleAIGetGeminiModel(),
            this.GoogleAIGetApiKey()),
        ServiceType.VertexAI => new VertexAIGeminiChatCompletionService(
            model: this.VertexAIGetGeminiModel(),
            apiKey: this.VertexAIGetApiKey(),
            location: this.VertexAIGetLocation(),
            projectId: this.VertexAIGetProjectId()),
        _ => throw new ArgumentOutOfRangeException(nameof(serviceType), serviceType, null)
    };

    protected IChatCompletionService GetChatServiceWithVision(ServiceType serviceType) => serviceType switch
    {
        ServiceType.GoogleAI => new GoogleAIGeminiChatCompletionService(
            this.GoogleAIGetGeminiVisionModel(),
            this.GoogleAIGetApiKey()),
        ServiceType.VertexAI => new VertexAIGeminiChatCompletionService(
            model: this.VertexAIGetGeminiVisionModel(),
            apiKey: this.VertexAIGetApiKey(),
            location: this.VertexAIGetLocation(),
            projectId: this.VertexAIGetProjectId()),
        _ => throw new ArgumentOutOfRangeException(nameof(serviceType), serviceType, null)
    };

    protected ITextGenerationService GetTextService(ServiceType serviceType) => serviceType switch
    {
        ServiceType.GoogleAI => new GoogleAIGeminiTextGenerationService(
            this.GoogleAIGetGeminiModel(),
            this.GoogleAIGetApiKey()),
        ServiceType.VertexAI => new VertexAIGeminiTextGenerationService(
            model: this.VertexAIGetGeminiModel(),
            apiKey: this.VertexAIGetApiKey(),
            location: this.VertexAIGetLocation(),
            projectId: this.VertexAIGetProjectId()),
        _ => throw new ArgumentOutOfRangeException(nameof(serviceType), serviceType, null)
    };

    protected ITextEmbeddingGenerationService GetEmbeddingService(ServiceType serviceType) => serviceType switch
    {
        ServiceType.GoogleAI => new GoogleAITextEmbeddingGenerationService(
            this.GoogleAIGetEmbeddingModel(),
            this.GoogleAIGetApiKey()),
        ServiceType.VertexAI => new VertexAITextEmbeddingGenerationService(
            model: this.VertexAIGetEmbeddingModel(),
            apiKey: this.VertexAIGetApiKey(),
            location: this.VertexAIGetLocation(),
            projectId: this.VertexAIGetProjectId()),
        _ => throw new ArgumentOutOfRangeException(nameof(serviceType), serviceType, null)
    };

    public enum ServiceType
    {
        GoogleAI,
        VertexAI
    }

    private string GoogleAIGetGeminiModel() => this._configuration.GetSection("GoogleAI:Gemini:ModelId").Get<string>()!;
    private string GoogleAIGetGeminiVisionModel() => this._configuration.GetSection("GoogleAI:Gemini:VisionModelId").Get<string>()!;
    private string GoogleAIGetEmbeddingModel() => this._configuration.GetSection("GoogleAI:EmbeddingModelId").Get<string>()!;
    private string GoogleAIGetApiKey() => this._configuration.GetSection("GoogleAI:ApiKey").Get<string>()!;
    private string VertexAIGetGeminiModel() => this._configuration.GetSection("VertexAI:Gemini:ModelId").Get<string>()!;
    private string VertexAIGetGeminiVisionModel() => this._configuration.GetSection("VertexAI:Gemini:VisionModelId").Get<string>()!;
    private string VertexAIGetEmbeddingModel() => this._configuration.GetSection("VertexAI:EmbeddingModelId").Get<string>()!;
    private string VertexAIGetApiKey() => this._configuration.GetSection("VertexAI:ApiKey").Get<string>()!;
    private string VertexAIGetLocation() => this._configuration.GetSection("VertexAI:Location").Get<string>()!;
    private string VertexAIGetProjectId() => this._configuration.GetSection("VertexAI:ProjectId").Get<string>()!;
}
