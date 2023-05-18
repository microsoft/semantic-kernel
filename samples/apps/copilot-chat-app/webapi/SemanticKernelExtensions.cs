// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Connectors.Memory.AzureCognitiveSearch;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;
using Microsoft.SemanticKernel.CoreSkills;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.TemplateEngine;
using SemanticKernel.Service.CopilotChat.Extensions;
using SemanticKernel.Service.Options;

namespace SemanticKernel.Service;

/// <summary>
/// Extension methods for registering Semantic Kernel related services.
/// </summary>
internal static class SemanticKernelExtensions
{
    /// <summary>
    /// Delegate to register skills with a Semantic Kernel
    /// </summary>
    public delegate Task RegisterSkillsWithKernel(IServiceProvider sp, IKernel kernel);

    /// <summary>
    /// Add Semantic Kernel services
    /// </summary>
    internal static IServiceCollection AddSemanticKernelServices(this IServiceCollection services)
    {
        // Semantic Kernel
        services.AddScoped<IKernel>(sp =>
        {
            IKernel kernel = Kernel.Builder
                .WithLogger(sp.GetRequiredService<ILogger<IKernel>>())
                .WithMemory(sp.GetRequiredService<ISemanticTextMemory>())
                .WithConfiguration(sp.GetRequiredService<KernelConfig>())
                .Build();

            sp.GetRequiredService<RegisterSkillsWithKernel>()(sp, kernel);
            return kernel;
        });

        // Semantic memory
        services.AddSemanticTextMemory();

        // AI backends
        services.AddScoped<KernelConfig>(serviceProvider => new KernelConfig()
            .AddCompletionBackend(serviceProvider.GetRequiredService<IOptionsSnapshot<AIServiceOptions>>()
                .Get(AIServiceOptions.CompletionPropertyName))
            .AddEmbeddingBackend(serviceProvider.GetRequiredService<IOptionsSnapshot<AIServiceOptions>>()
                .Get(AIServiceOptions.EmbeddingPropertyName)));

        // Register skills
        services.AddScoped<RegisterSkillsWithKernel>(sp => RegisterSkills);

        return services;
    }

    /// <summary>
    /// Register the skills with the kernel.
    /// </summary>
    private static Task RegisterSkills(IServiceProvider sp, IKernel kernel)
    {
        // Copilot chat skills
        kernel.RegisterCopilotChatSkills(sp);

        // Time skill
        kernel.ImportSkill(new TimeSkill(), nameof(TimeSkill));

        // Semantic skills
        ServiceOptions options = sp.GetRequiredService<IOptions<ServiceOptions>>().Value;
        if (!string.IsNullOrWhiteSpace(options.SemanticSkillsDirectory))
        {
            foreach (string subDir in Directory.GetDirectories(options.SemanticSkillsDirectory))
            {
                try
                {
                    kernel.ImportSemanticSkillFromDirectory(options.SemanticSkillsDirectory, Path.GetFileName(subDir)!);
                }
                catch (TemplateException e)
                {
                    kernel.Log.LogError("Could not load skill from {Directory}: {Message}", subDir, e.Message);
                }
            }
        }

        return Task.CompletedTask;
    }

    /// <summary>
    /// Add the semantic memory.
    /// </summary>
    private static void AddSemanticTextMemory(this IServiceCollection services)
    {
        MemoriesStoreOptions config = services.BuildServiceProvider().GetRequiredService<IOptions<MemoriesStoreOptions>>().Value;
        switch (config.Type)
        {
            case MemoriesStoreOptions.MemoriesStoreType.Volatile:
                services.AddSingleton<IMemoryStore, VolatileMemoryStore>();
                services.AddScoped<ISemanticTextMemory>(sp => new SemanticTextMemory(
                    sp.GetRequiredService<IMemoryStore>(),
                    sp.GetRequiredService<IOptionsSnapshot<AIServiceOptions>>().Get(AIServiceOptions.EmbeddingPropertyName)
                        .ToTextEmbeddingsService(logger: sp.GetRequiredService<ILogger<AIServiceOptions>>())));
                break;

            case MemoriesStoreOptions.MemoriesStoreType.Qdrant:
                if (config.Qdrant == null)
                {
                    throw new InvalidOperationException("MemoriesStore type is Qdrant and Qdrant configuration is null.");
                }

                services.AddSingleton<IMemoryStore>(sp => new QdrantMemoryStore(
                    config.Qdrant.Host, config.Qdrant.Port, config.Qdrant.VectorSize, sp.GetRequiredService<ILogger<QdrantMemoryStore>>()));
                services.AddScoped<ISemanticTextMemory>(sp => new SemanticTextMemory(
                    sp.GetRequiredService<IMemoryStore>(),
                    sp.GetRequiredService<IOptionsSnapshot<AIServiceOptions>>().Get(AIServiceOptions.EmbeddingPropertyName)
                        .ToTextEmbeddingsService(logger: sp.GetRequiredService<ILogger<AIServiceOptions>>())));
                break;

            case MemoriesStoreOptions.MemoriesStoreType.AzureCognitiveSearch:
                if (config.AzureCognitiveSearch == null)
                {
                    throw new InvalidOperationException("MemoriesStore type is AzureCognitiveSearch and AzureCognitiveSearch configuration is null.");
                }

                services.AddSingleton<ISemanticTextMemory>(sp => new AzureCognitiveSearchMemory(config.AzureCognitiveSearch.Endpoint, config.AzureCognitiveSearch.Key));
                break;

            default:
                throw new InvalidOperationException($"Invalid 'MemoriesStore' type '{config.Type}'.");
        }
    }

    /// <summary>
    /// Add the completion backend to the kernel config
    /// </summary>
    private static KernelConfig AddCompletionBackend(this KernelConfig kernelConfig, AIServiceOptions aiServiceOptions)
    {
        switch (aiServiceOptions.AIService)
        {
            case AIServiceOptions.AIServiceType.AzureOpenAI:
                kernelConfig.AddAzureChatCompletionService(
                    deploymentName: aiServiceOptions.DeploymentOrModelId,
                    endpoint: aiServiceOptions.Endpoint,
                    apiKey: aiServiceOptions.Key);
                break;

            case AIServiceOptions.AIServiceType.OpenAI:
                kernelConfig.AddOpenAIChatCompletionService(
                    modelId: aiServiceOptions.DeploymentOrModelId,
                    apiKey: aiServiceOptions.Key);
                break;

            default:
                throw new ArgumentException($"Invalid {nameof(aiServiceOptions.AIService)} value in '{AIServiceOptions.CompletionPropertyName}' settings.");
        }

        return kernelConfig;
    }

    /// <summary>
    /// Add the embedding backend to the kernel config
    /// </summary>
    private static KernelConfig AddEmbeddingBackend(this KernelConfig kernelConfig, AIServiceOptions aiServiceOptions)
    {
        switch (aiServiceOptions.AIService)
        {
            case AIServiceOptions.AIServiceType.AzureOpenAI:
                kernelConfig.AddAzureTextEmbeddingGenerationService(
                    deploymentName: aiServiceOptions.DeploymentOrModelId,
                    endpoint: aiServiceOptions.Endpoint,
                    apiKey: aiServiceOptions.Key,
                    serviceId: aiServiceOptions.Label);
                break;

            case AIServiceOptions.AIServiceType.OpenAI:
                kernelConfig.AddOpenAITextEmbeddingGenerationService(
                    modelId: aiServiceOptions.DeploymentOrModelId,
                    apiKey: aiServiceOptions.Key,
                    serviceId: aiServiceOptions.Label);
                break;

            default:
                throw new ArgumentException($"Invalid {nameof(aiServiceOptions.AIService)} value in '{AIServiceOptions.EmbeddingPropertyName}' settings.");
        }

        return kernelConfig;
    }

    /// <summary>
    /// Construct IEmbeddingGeneration from <see cref="AIServiceOptions"/>
    /// </summary>
    /// <param name="serviceConfig">The service configuration</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    private static IEmbeddingGeneration<string, float> ToTextEmbeddingsService(this AIServiceOptions serviceConfig,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        return serviceConfig.AIService switch
        {
            AIServiceOptions.AIServiceType.AzureOpenAI => new AzureTextEmbeddingGeneration(
                serviceConfig.DeploymentOrModelId,
                serviceConfig.Endpoint,
                serviceConfig.Key,
                httpClient: httpClient,
                logger: logger),

            AIServiceOptions.AIServiceType.OpenAI => new OpenAITextEmbeddingGeneration(
                serviceConfig.DeploymentOrModelId,
                serviceConfig.Key,
                httpClient: httpClient,
                logger: logger),

            _ => throw new ArgumentException("Invalid AIService value in embeddings backend settings"),
        };
    }
}
