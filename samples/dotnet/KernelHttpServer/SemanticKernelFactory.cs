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
        IMemoryStore<float>? memoryStore = null)
    {
        var apiConfig = req.ToApiKeyConfig();

        //must have a completion backend
        if (!apiConfig.CompletionConfig.IsValid())
        {
            logger.LogError("Completion backend has not been supplied.");
            return null;
        }

        //embedding backend is optional, don't fail if we were not given the config
        if (memoryStore != null &&
            !apiConfig.EmbeddingConfig.IsValid())
        {
            logger.LogWarning("Embedding backend has not been supplied.");
        }

        KernelBuilder builder = Kernel.Builder;
        builder = _ConfigureKernelBuilder(apiConfig, builder, memoryStore);
        return _CompleteKernelSetup(req, builder, logger, skillsToLoad);
    }

    private static KernelBuilder _ConfigureKernelBuilder(ApiKeyConfig config, KernelBuilder builder, IMemoryStore<float>? memoryStore)
    {
        builder = builder
            .Configure(c =>
            {
                switch (config.CompletionConfig.AIService)
                {
                    case AIService.OpenAI:
                        c.AddOpenAICompletionBackend(config.CompletionConfig.Label, config.CompletionConfig.DeploymentOrModelId, config.CompletionConfig.Key);
                        break;
                    case AIService.AzureOpenAI:
                        c.AddAzureOpenAICompletionBackend(config.CompletionConfig.Label, config.CompletionConfig.DeploymentOrModelId, config.CompletionConfig.Endpoint, config.CompletionConfig.Key);
                        break;
                }

                if (memoryStore != null && config.EmbeddingConfig.IsValid())
                {
                    switch (config.EmbeddingConfig.AIService)
                    {
                        case AIService.OpenAI:
                            c.AddOpenAIEmbeddingsBackend(config.EmbeddingConfig.Label, config.EmbeddingConfig.DeploymentOrModelId, config.EmbeddingConfig.Key);
                            break;
                        case AIService.AzureOpenAI:
                            c.AddAzureOpenAIEmbeddingsBackend(config.EmbeddingConfig.Label, config.EmbeddingConfig.DeploymentOrModelId, config.EmbeddingConfig.Endpoint, config.EmbeddingConfig.Key);
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
