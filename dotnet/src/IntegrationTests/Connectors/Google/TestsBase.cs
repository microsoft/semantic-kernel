// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Embeddings;
using Xunit.Abstractions;

namespace SemanticKernel.IntegrationTests.Connectors.Google;

public abstract class TestsBase
{
    private readonly IConfigurationRoot _configuration;
    protected ITestOutputHelper Output { get; }
    private readonly GoogleAIConfig _googleAI;
    private readonly VertexAIConfig _vertexAI;

    protected GoogleAIConfig GoogleAI => this._googleAI;
    protected VertexAIConfig VertexAI => this._vertexAI;

    protected TestsBase(ITestOutputHelper output)
    {
        this.Output = output;
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
            .AddUserSecrets<TestsBase>()
            .AddEnvironmentVariables()
            .Build();

        this._googleAI = new GoogleAIConfig();
        this._vertexAI = new VertexAIConfig();

        this._configuration.GetSection("GoogleAI").Bind(this._googleAI);
        this._configuration.GetSection("VertexAI").Bind(this._vertexAI);
    }

    protected IChatCompletionService GetChatService(ServiceType serviceType, bool isBeta = false, string? overrideModelId = null) => serviceType switch
    {
        ServiceType.GoogleAI => new GoogleAIGeminiChatCompletionService(
            overrideModelId ?? this.GoogleAI.Gemini.ModelId,
            this.GoogleAI.ApiKey,
            isBeta ? GoogleAIVersion.V1_Beta : GoogleAIVersion.V1),
        ServiceType.VertexAI => new VertexAIGeminiChatCompletionService(
            modelId: overrideModelId ?? this.VertexAI.Gemini.ModelId,
            bearerKey: this.VertexAI.BearerKey,
            location: this.VertexAI.Location,
            projectId: this.VertexAI.ProjectId,
            isBeta ? VertexAIVersion.V1_Beta : VertexAIVersion.V1),
        _ => throw new ArgumentOutOfRangeException(nameof(serviceType), serviceType, null)
    };

    protected IChatCompletionService GetChatServiceWithVision(ServiceType serviceType) => serviceType switch
    {
        ServiceType.GoogleAI => new GoogleAIGeminiChatCompletionService(
            this.GoogleAI.Gemini.VisionModelId,
            this.GoogleAI.ApiKey),
        ServiceType.VertexAI => new VertexAIGeminiChatCompletionService(
            modelId: this.VertexAI.Gemini.VisionModelId,
            bearerKey: this.VertexAI.BearerKey,
            location: this.VertexAI.Location,
            projectId: this.VertexAI.ProjectId),
        _ => throw new ArgumentOutOfRangeException(nameof(serviceType), serviceType, null)
    };

    protected ITextEmbeddingGenerationService GetEmbeddingService(ServiceType serviceType) => serviceType switch
    {
        ServiceType.GoogleAI => new GoogleAITextEmbeddingGenerationService(
            this.GoogleAI.EmbeddingModelId,
            this.GoogleAI.ApiKey),
        ServiceType.VertexAI => new VertexAITextEmbeddingGenerationService(
            modelId: this.VertexAI.EmbeddingModelId,
            bearerKey: this.VertexAI.BearerKey,
            location: this.VertexAI.Location,
            projectId: this.VertexAI.ProjectId),
        _ => throw new ArgumentOutOfRangeException(nameof(serviceType), serviceType, null)
    };

    protected ITextEmbeddingGenerationService GetEmbeddingServiceWithDimensions(ServiceType serviceType, int dimensions) => serviceType switch
    {
        ServiceType.GoogleAI => new GoogleAITextEmbeddingGenerationService(
            this.GoogleAI.EmbeddingModelId,
            this.GoogleAI.ApiKey,
            dimensions: dimensions),
        ServiceType.VertexAI => throw new NotImplementedException("Semantic Kernel does not support configuring dimensions for Vertex AI embeddings"),
        _ => throw new ArgumentException($"Invalid service type: {serviceType}", nameof(serviceType))
    };

    public enum ServiceType
    {
        GoogleAI,
        VertexAI
    }

    protected sealed class VertexAIConfig
    {
        public string ModelId { get; set; } = null!;
        public string BearerKey { get; set; } = null!;
        public string Location { get; set; } = null!;
        public string ProjectId { get; set; } = null!;
        public string EmbeddingModelId { get; set; } = null!;
        public GeminiConfig Gemini { get; set; } = new();
    }

    protected sealed class GoogleAIConfig
    {
        public string ApiKey { get; set; } = null!;
        public string EmbeddingModelId { get; set; } = null!;
        public GeminiConfig Gemini { get; set; } = new();
    }

    protected class GeminiConfig
    {
        public string ModelId { get; set; } = null!;
        public string VisionModelId { get; set; } = null!;
    }
}
