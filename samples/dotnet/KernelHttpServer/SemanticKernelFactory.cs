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
            logger.LogError("Text completion service has not been supplied");
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
        return builder.Configure(c =>
        {
            switch (config.CompletionConfig.AIService)
            {
                case AIService.OpenAI:
                    c.AddOpenAITextCompletionService(config.CompletionConfig.ServiceId, config.CompletionConfig.DeploymentOrModelId,
                        config.CompletionConfig.Key);
                    break;
                case AIService.AzureOpenAI:
                    c.AddAzureTextCompletionService(config.CompletionConfig.ServiceId, config.CompletionConfig.DeploymentOrModelId,
                        config.CompletionConfig.Endpoint,
                        config.CompletionConfig.Key);
                    break;
            }

            if (memoryStore != null && config.EmbeddingConfig.IsValid())
            {
                switch (config.EmbeddingConfig.AIService)
                {
                    case AIService.OpenAI:
                        c.AddOpenAITextEmbeddingGenerationService(config.EmbeddingConfig.ServiceId, config.EmbeddingConfig.DeploymentOrModelId,
                            config.EmbeddingConfig.Key);
                        break;
                    case AIService.AzureOpenAI:
                        c.AddAzureTextEmbeddingGenerationService(config.EmbeddingConfig.ServiceId, config.EmbeddingConfig.DeploymentOrModelId,
                            config.EmbeddingConfig.Endpoint, config.EmbeddingConfig.Key);
                        break;
                }

                builder.WithMemoryStorage(memoryStore);
            }
        });
    }

    private static IKernel _CompleteKernelSetup(HttpRequestData req, KernelBuilder builder, ILogger logger, IEnumerable<string>? skillsToLoad = null)
    {
        IKernel kernel = builder.Build();

        kernel.RegisterSemanticSkills(RepoFiles.SampleSkillsPath(), logger, skillsToLoad);
        kernel.RegisterNativeSkills(skillsToLoad);
        kernel.RegisterPlanner();

        if (req.Headers.TryGetValues(SKHttpHeaders.MSGraph, out var graphToken))
        {
            kernel.RegisterNativeGraphSkills(graphToken.First());
        }

        if (kernel.Config.DefaultTextEmbeddingGenerationServiceId != null)
        {
            kernel.RegisterTextMemory();
        }

        return kernel;
    }
}
