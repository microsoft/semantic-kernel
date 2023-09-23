// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using KernelHttpServer.Config;
using KernelHttpServer.Utils;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using static KernelHttpServer.Config.Constants;

namespace KernelHttpServer;

internal static class SemanticKernelFactory
{
    internal static IKernel? CreateForRequest(
        HttpRequestData req,
        ILogger logger,
        IEnumerable<string>? skillsToLoad = null,
        IMemoryStore? memoryStore = null)
    {
        var apiConfig = req.ToApiKeyConfig();

        // must have a completion service
        if (!apiConfig.CompletionConfig.IsValid())
        {
            logger.LogError("Chat completion service has not been supplied");
            return null;
        }

        // Text embedding service is optional, don't fail if we were not given the config
        if (memoryStore != null &&
            !apiConfig.EmbeddingConfig.IsValid())
        {
            logger.LogWarning("Text embedding service has not been supplied");
        }

        KernelBuilder builder = Kernel.Builder;
        builder = _ConfigureKernelBuilder(apiConfig, builder, memoryStore);
        return _CompleteKernelSetup(req, builder, logger, skillsToLoad);
    }

    private static KernelBuilder _ConfigureKernelBuilder(ApiKeyConfig config, KernelBuilder builder, IMemoryStore? memoryStore)
    {
        switch (config.CompletionConfig.AIService)
        {
            case AIService.OpenAI:
                builder.WithOpenAIChatCompletionService(
                    modelId: config.CompletionConfig.DeploymentOrModelId,
                    apiKey: config.CompletionConfig.Key);
                break;
            case AIService.AzureOpenAI:
                builder.WithAzureChatCompletionService(
                    deploymentName: config.CompletionConfig.DeploymentOrModelId,
                    endpoint: config.CompletionConfig.Endpoint,
                    apiKey: config.CompletionConfig.Key);
                break;
            default:
                break;
        }

        if (memoryStore != null && config.EmbeddingConfig.IsValid())
        {
            switch (config.EmbeddingConfig.AIService)
            {
                case AIService.OpenAI:
                    builder.WithOpenAITextEmbeddingGenerationService(
                        modelId: config.EmbeddingConfig.DeploymentOrModelId,
                        apiKey: config.EmbeddingConfig.Key);
                    break;
                case AIService.AzureOpenAI:
                    builder.WithAzureTextEmbeddingGenerationService(
                        deploymentName: config.EmbeddingConfig.DeploymentOrModelId,
                        endpoint: config.EmbeddingConfig.Endpoint,
                        apiKey: config.EmbeddingConfig.Key);
                    break;
                default:
                    break;
            }

            builder.WithMemoryStorage(memoryStore);
        }

        return builder;
    }

    private static IKernel _CompleteKernelSetup(HttpRequestData req, KernelBuilder builder, ILogger logger, IEnumerable<string>? skillsToLoad = null)
    {
        IKernel kernel = builder.Build();

        kernel.RegisterSemanticFunctions(RepoFiles.SampleSkillsPath(), logger, skillsToLoad);
        kernel.RegisterNativePlugins(skillsToLoad);

        if (req.Headers.TryGetValues(SKHttpHeaders.MSGraph, out var graphToken))
        {
            kernel.RegisterNativeGraphPlugins(graphToken.First());
        }

        kernel.RegisterTextMemory();

        return kernel;
    }
}
