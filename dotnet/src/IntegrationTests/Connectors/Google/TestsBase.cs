// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Embeddings;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Google;

public abstract class TestsBase(ITestOutputHelper output)
{
    private readonly IConfigurationRoot _configuration = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddUserSecrets<TestsBase>()
        .AddEnvironmentVariables()
        .Build();

    protected ITestOutputHelper Output { get; } = output;

    protected IChatCompletionService GetChatService(ServiceType serviceType, bool isBeta = false) => serviceType switch
    {
        ServiceType.GoogleAI => new GoogleAIGeminiChatCompletionService(
            this.GoogleAIGetGeminiModel(),
            this.GoogleAIGetApiKey(),
            isBeta ? GoogleAIVersion.V1_Beta : GoogleAIVersion.V1),
        ServiceType.VertexAI => new VertexAIGeminiChatCompletionService(
            modelId: this.VertexAIGetGeminiModel(),
            bearerKey: this.VertexAIGetBearerKey(),
            location: this.VertexAIGetLocation(),
            projectId: this.VertexAIGetProjectId(),
            isBeta ? VertexAIVersion.V1_Beta : VertexAIVersion.V1),
        _ => throw new ArgumentOutOfRangeException(nameof(serviceType), serviceType, null)
    };

    protected IChatCompletionService GetChatServiceWithVision(ServiceType serviceType) => serviceType switch
    {
        ServiceType.GoogleAI => new GoogleAIGeminiChatCompletionService(
            this.GoogleAIGetGeminiVisionModel(),
            this.GoogleAIGetApiKey()),
        ServiceType.VertexAI => new VertexAIGeminiChatCompletionService(
            modelId: this.VertexAIGetGeminiVisionModel(),
            bearerKey: this.VertexAIGetBearerKey(),
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
            modelId: this.VertexAIGetEmbeddingModel(),
            bearerKey: this.VertexAIGetBearerKey(),
            location: this.VertexAIGetLocation(),
            projectId: this.VertexAIGetProjectId()),
        _ => throw new ArgumentOutOfRangeException(nameof(serviceType), serviceType, null)
    };

    protected ITextEmbeddingGenerationService GetEmbeddingServiceWithDimensions(ServiceType serviceType, int dimensions) => serviceType switch
    {
        ServiceType.GoogleAI => new GoogleAITextEmbeddingGenerationService(
            this.GoogleAIGetEmbeddingModel(),
            this.GoogleAIGetApiKey(),
            dimensions: dimensions),
        ServiceType.VertexAI => throw new NotImplementedException("Semantic Kernel does not support configuring dimensions for Vertex AI embeddings"),
        _ => throw new ArgumentException($"Invalid service type: {serviceType}", nameof(serviceType))
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
    internal string VertexAIGetGeminiModel() => this._configuration.GetSection("VertexAI:Gemini:ModelId").Get<string>()!;
    private string VertexAIGetGeminiVisionModel() => this._configuration.GetSection("VertexAI:Gemini:VisionModelId").Get<string>()!;
    private string VertexAIGetEmbeddingModel() => this._configuration.GetSection("VertexAI:EmbeddingModelId").Get<string>()!;
    internal string VertexAIGetBearerKey() => this._configuration.GetSection("VertexAI:BearerKey").Get<string>()!;
    internal string VertexAIGetLocation() => this._configuration.GetSection("VertexAI:Location").Get<string>()!;
    internal string VertexAIGetProjectId() => this._configuration.GetSection("VertexAI:ProjectId").Get<string>()!;
}
