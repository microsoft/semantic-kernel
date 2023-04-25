// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using System.Text.Json;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Reliability;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
using SemanticKernel.Service.Config;
using SemanticKernel.Service.Skills;

namespace SemanticKernel.Service;

internal static class SemanticKernelExtensions
{
    /// <summary>
    /// Add Semantic Kernel services
    /// </summary>
    internal static IServiceCollection AddSemanticKernelServices(this IServiceCollection services)
    {
        // The chat skill's prompts are stored in a separate file.
        services.AddSingleton<PromptsConfig>(sp =>
        {
            string promptsConfigPath = Path.Combine(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location)!, "prompts.json");
            PromptsConfig promptsConfig = JsonSerializer.Deserialize<PromptsConfig>(File.ReadAllText(promptsConfigPath)) ??
                                            throw new InvalidOperationException($"Failed to load '{promptsConfigPath}'.");
            promptsConfig.Validate();
            return promptsConfig;
        });
        services.AddSingleton<PromptSettings>();

        services.AddSingleton<IMemoryStore>(serviceProvider =>
        {
            MemoriesStoreOptions config = serviceProvider.GetRequiredService<IOptions<MemoriesStoreOptions>>().Value;

            switch (config.Type)
            {
                case MemoriesStoreOptions.MemoriesStoreType.Volatile:
                    return new VolatileMemoryStore();

                case MemoriesStoreOptions.MemoriesStoreType.Qdrant:
                    if (config.Qdrant is null)
                    {
                        throw new InvalidOperationException($"MemoriesStore:Qdrant is required when MemoriesStore:Type is '{MemoriesStoreOptions.MemoriesStoreType.Qdrant}'");
                    }

                    return new QdrantMemoryStore(
                        host: config.Qdrant.Host,
                        port: config.Qdrant.Port,
                        vectorSize: config.Qdrant.VectorSize,
                        logger: serviceProvider.GetRequiredService<ILogger<QdrantMemoryStore>>());

                default:
                    throw new InvalidOperationException($"Invalid 'MemoriesStore' type '{config.Type}'.");
            }
        });

        services.AddScoped<ISemanticTextMemory>(serviceProvider => new SemanticTextMemory(
                serviceProvider.GetRequiredService<IMemoryStore>(),
                serviceProvider.GetRequiredService<IOptionsSnapshot<AIServiceOptions>>().Get(AIServiceOptions.EmbeddingPropertyName)
                    .ToTextEmbeddingsService(serviceProvider.GetRequiredService<ILogger<AIServiceOptions>>())));


        // Add the Semantic Kernel
        services.AddSingleton<IPromptTemplateEngine, PromptTemplateEngine>();
        services.AddScoped<ISkillCollection, SkillCollection>();
        services.AddScoped<KernelConfig>(serviceProvider => new KernelConfig()
                    .AddCompletionBackend(serviceProvider.GetRequiredService<IOptionsSnapshot<AIServiceOptions>>())
                    .AddEmbeddingBackend(serviceProvider.GetRequiredService<IOptionsSnapshot<AIServiceOptions>>()));
        services.AddScoped<IKernel, Kernel>();

        return services;
    }

    /// <summary>
    /// Add the completion backend to the kernel config
    /// </summary>
    internal static KernelConfig AddCompletionBackend(this KernelConfig kernelConfig, IOptionsSnapshot<AIServiceOptions> aiServiceOptions)
    {
        AIServiceOptions config = aiServiceOptions.Get(AIServiceOptions.CompletionPropertyName);

        switch (config.AIService)
        {
            case AIServiceOptions.AIServiceType.AzureOpenAI:
                kernelConfig.AddAzureChatCompletionService(
                    serviceId: config.Label,
                    deploymentName: config.DeploymentOrModelId,
                    endpoint: config.Endpoint,
                    apiKey: config.Key,
                    alsoAsTextCompletion: true);
                break;

            case AIServiceOptions.AIServiceType.OpenAI:
                kernelConfig.AddOpenAIChatCompletionService(
                    serviceId: config.Label,
                    modelId: config.DeploymentOrModelId,
                    apiKey: config.Key,
                    alsoAsTextCompletion: true);
                break;

            default:
                throw new ArgumentException($"Invalid {nameof(config.AIService)} value in '{AIServiceOptions.CompletionPropertyName}' settings.");
        }

        return kernelConfig;
    }

    /// <summary>
    /// Add the embedding backend to the kernel config
    /// </summary>
    internal static KernelConfig AddEmbeddingBackend(this KernelConfig kernelConfig, IOptionsSnapshot<AIServiceOptions> aiServiceOptions)
    {
        AIServiceOptions config = aiServiceOptions.Get(AIServiceOptions.EmbeddingPropertyName);

        switch (config.AIService)
        {
            case AIServiceOptions.AIServiceType.AzureOpenAI:
                kernelConfig.AddAzureTextEmbeddingGenerationService(
                    serviceId: config.Label,
                    deploymentName: config.DeploymentOrModelId,
                    endpoint: config.Endpoint,
                    apiKey: config.Key);
                break;

            case AIServiceOptions.AIServiceType.OpenAI:
                kernelConfig.AddOpenAITextEmbeddingGenerationService(
                    serviceId: config.Label,
                    modelId: config.DeploymentOrModelId,
                    apiKey: config.Key);
                break;

            default:
                throw new ArgumentException($"Invalid {nameof(config.AIService)} value in '{AIServiceOptions.EmbeddingPropertyName}' settings.");
        }

        return kernelConfig;
    }

    /// <summary>
    /// Construct IEmbeddingGeneration from <see cref="AIServiceOptions"/>
    /// </summary>
    internal static IEmbeddingGeneration<string, float> ToTextEmbeddingsService(this AIServiceOptions serviceConfig,
        ILogger? logger = null,
        IDelegatingHandlerFactory? handlerFactory = null)
    {

        return serviceConfig.AIService switch
        {
            AIServiceOptions.AIServiceType.AzureOpenAI => new AzureTextEmbeddingGeneration(
                serviceConfig.DeploymentOrModelId,
                serviceConfig.Endpoint,
                serviceConfig.Key,
                handlerFactory: handlerFactory,
                log: logger),

            AIServiceOptions.AIServiceType.OpenAI => new OpenAITextEmbeddingGeneration(
                serviceConfig.DeploymentOrModelId, serviceConfig.Key, handlerFactory: handlerFactory, log: logger),

            _ => throw new ArgumentException("Invalid AIService value in embeddings backend settings"),
        };
    }
}
