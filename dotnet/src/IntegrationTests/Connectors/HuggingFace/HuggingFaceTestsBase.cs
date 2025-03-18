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

public abstract class HuggingFaceTestsBase
{
    private readonly IConfigurationRoot _configuration;
    protected ITestOutputHelper Output { get; }

    protected HuggingFaceConfig Config { get; }

    protected HuggingFaceTestsBase(ITestOutputHelper output)
    {
        this.Output = output;
        this._configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
            .AddUserSecrets<HuggingFaceTestsBase>()
            .AddEnvironmentVariables()
            .Build();

        this.Config = this._configuration.GetSection("HuggingFace").Get<HuggingFaceConfig>()!;
    }

    protected IChatCompletionService CreateChatCompletionService() =>
        new HuggingFaceChatCompletionService(
            model: this.Config.ChatCompletionModelId,
            endpoint: new Uri(this.Config.ChatCompletionEndpoint),
            apiKey: this.Config.ApiKey);

    protected ITextGenerationService CreateTextGenerationService(Uri? endpoint = null, HttpClient? httpClient = null) =>
        new HuggingFaceTextGenerationService(
            model: this.Config.TextGenerationModelId,
            endpoint: endpoint ?? new Uri(this.Config.TextGenerationEndpoint),
            apiKey: this.Config.ApiKey,
            httpClient: httpClient);

    protected ITextEmbeddingGenerationService CreateEmbeddingService() =>
        new HuggingFaceTextEmbeddingGenerationService(
            model: this.Config.EmbeddingModelId,
            endpoint: new Uri(this.Config.EmbeddingEndpoint),
            apiKey: this.Config.ApiKey);

    protected Kernel CreateKernelWithChatCompletion() =>
        Kernel.CreateBuilder()
            .AddHuggingFaceChatCompletion(
                model: this.Config.ChatCompletionModelId,
                endpoint: new Uri(this.Config.ChatCompletionEndpoint),
                apiKey: this.Config.ApiKey)
            .Build();

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
    protected sealed class HuggingFaceConfig
    {
        public string ApiKey { get; set; }
        public string ChatCompletionModelId { get; set; }
        public string TextGenerationEndpoint { get; set; }
        public string TextGenerationModelId { get; set; }
        public string EmbeddingModelId { get; set; }
        public string EmbeddingEndpoint { get; set; }
        public string ChatCompletionEndpoint { get; set; }
    }
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
}
