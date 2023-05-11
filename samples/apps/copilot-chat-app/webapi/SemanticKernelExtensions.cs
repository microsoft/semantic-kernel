// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using System.Text.Json;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Connectors.Memory.AzureCognitiveSearch;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;
using Microsoft.SemanticKernel.Memory;
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
        // Load the chat skill's prompts from the prompt configuration file.
        services.AddSingleton<PromptsConfig>(sp =>
        {
            string promptsConfigPath = Path.Combine(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location)!, "prompts.json");
            PromptsConfig promptsConfig = JsonSerializer.Deserialize<PromptsConfig>(
                File.ReadAllText(promptsConfigPath), new JsonSerializerOptions() { ReadCommentHandling = JsonCommentHandling.Skip })
                ?? throw new InvalidOperationException($"Failed to load '{promptsConfigPath}'.");
            promptsConfig.Validate();
            return promptsConfig;
        });
        services.AddSingleton<PromptSettings>();

        // Add the semantic memory with backing memory store.
        services.AddSemanticTextMemory();

        // Add the planner.
        services.AddScoped<CopilotChatPlanner>(sp =>
        {
            // Create a kernel for the planner with the same contexts as the chat's kernel except with no skills and its own completion backend.
            // This allows the planner to use only the skills that are available at call time.
            IKernel chatKernel = sp.GetRequiredService<IKernel>();
            IOptions<PlannerOptions> plannerOptions = sp.GetRequiredService<IOptions<PlannerOptions>>();
            IKernel plannerKernel = new Kernel(
                new SkillCollection(),
                chatKernel.PromptTemplateEngine,
                chatKernel.Memory,
                new KernelConfig().AddCompletionBackend(plannerOptions.Value.AIService!),
                sp.GetRequiredService<ILogger<CopilotChatPlanner>>());
            return new CopilotChatPlanner(plannerKernel, plannerOptions);
        });

        // Add the Semantic Kernel
        services.AddSingleton<IPromptTemplateEngine, PromptTemplateEngine>();
        services.AddScoped<ISkillCollection, SkillCollection>();
        services.AddScoped<KernelConfig>(serviceProvider => new KernelConfig()
            .AddCompletionBackend(serviceProvider.GetRequiredService<IOptionsSnapshot<AIServiceOptions>>()
                .Get(AIServiceOptions.CompletionPropertyName))
            .AddEmbeddingBackend(serviceProvider.GetRequiredService<IOptionsSnapshot<AIServiceOptions>>()
                .Get(AIServiceOptions.EmbeddingPropertyName)));
        services.AddScoped<IKernel, Kernel>();

        return services;
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
