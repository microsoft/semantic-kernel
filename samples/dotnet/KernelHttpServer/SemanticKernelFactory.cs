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
        VolatileMemoryStore? memoryStore = null)
    {
        var apiConfig = req.ToApiKeyConfig();

        //must have a completion backend (embedding is optional)
        if (!apiConfig.CompletionConfig.IsValid())
        {
            logger.LogWarning("Completion backend has not been supplied.");
            return null;
        }

        if (memoryStore != null &&
            !apiConfig.EmbeddingConfig.IsValid())
        {
            logger.LogWarning("Embedding backend has not been supplied.");
            return null;
        }

        KernelBuilder builder = Kernel.Builder;
        builder = _ConfigureKernelBuilder(apiConfig, builder, memoryStore);
        return _CompleteKernelSetup(req, builder, logger, skillsToLoad);
    }

    private static KernelBuilder _ConfigureKernelBuilder(ApiKeyConfig config, KernelBuilder builder, VolatileMemoryStore? memoryStore)
    {
        builder = builder
            .Configure(c =>
            {
                switch (config.CompletionConfig.AIService)
                {
                    case AIService.AzureOpenAI:
                        c.AddOpenAICompletionBackend(config.CompletionConfig.Label, config.CompletionConfig.DeploymentOrModelId, config.CompletionConfig.Key);
                        break;
                    case AIService.OpenAI:
                        c.AddAzureOpenAICompletionBackend(config.CompletionConfig.Label, config.CompletionConfig.DeploymentOrModelId, config.CompletionConfig.Endpoint, config.CompletionConfig.Key);
                        break;
                }

                if (memoryStore != null)
                {
                    switch (config.EmbeddingConfig.AIService)
                    {
                        case AIService.AzureOpenAI:
                            c.AddOpenAICompletionBackend(config.EmbeddingConfig.Label, config.EmbeddingConfig.DeploymentOrModelId, config.EmbeddingConfig.Key);
                            break;
                        case AIService.OpenAI:
                            c.AddAzureOpenAICompletionBackend(config.EmbeddingConfig.Label, config.EmbeddingConfig.DeploymentOrModelId, config.EmbeddingConfig.Endpoint, config.EmbeddingConfig.Key);
                            break;
                    }

                    builder.WithMemoryStorage(memoryStore);
                }
            });

        return builder;
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

        if (kernel.Config.DefaultEmbeddingsBackend != null)
        {
            kernel.RegisterTextMemory();
        }

        return kernel;
    }
}
