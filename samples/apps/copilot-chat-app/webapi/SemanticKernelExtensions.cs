// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using System.Text.Json;
using Microsoft.Extensions.Options;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;
using Microsoft.SemanticKernel.Memory;
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

        // Add the semantic memory with backing memory store.
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
                        throw new InvalidOperationException(
                            $"MemoriesStore:Qdrant is required when MemoriesStore:Type is '{MemoriesStoreOptions.MemoriesStoreType.Qdrant}'");
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

        services.AddScoped<ISemanticTextMemory>(serviceProvider
            => new SemanticTextMemory(
                serviceProvider.GetRequiredService<IMemoryStore>(),
                serviceProvider.GetRequiredService<IOptionsSnapshot<AIServiceOptions>>().Get(AIServiceOptions.EmbeddingPropertyName)
                    .ToTextEmbeddingsService(logger: serviceProvider.GetRequiredService<ILogger<AIServiceOptions>>())));

        // Add the planner.
        services.AddScoped<CopilotChatPlanner>(serviceProvider =>
        {
            // Create a kernel for the planner with the same contexts as the chat's kernel except with no skills and its own completion backend.
            // This allows the planner to use only the skills that are available at call time.
            IKernel chatKernel = serviceProvider.GetRequiredService<IKernel>();

            IOptions<PlannerOptions> plannerOptions = serviceProvider.GetRequiredService<IOptions<PlannerOptions>>();

            IKernel plannerKernel = Kernel.Builder
                .WithLogger(serviceProvider.GetRequiredService<ILogger<CopilotChatPlanner>>())
                .WithCompletionBackend(plannerOptions.Value.AIService!)
                .WithPromptTemplateEngine(chatKernel.PromptTemplateEngine)
                .WithMemory(chatKernel.Memory)
                .Build();

            return new CopilotChatPlanner(plannerKernel, plannerOptions);
        });

        // Add the Semantic Kernel
        services.AddScoped<IKernel>(serviceProvider =>
            new KernelBuilder()
                .WithCompletionBackend(serviceProvider.GetRequiredService<IOptionsSnapshot<AIServiceOptions>>().Get(AIServiceOptions.CompletionPropertyName))
                .WithEmbeddingBackend(serviceProvider.GetRequiredService<IOptionsSnapshot<AIServiceOptions>>().Get(AIServiceOptions.EmbeddingPropertyName))
                .WithMemory(serviceProvider.GetRequiredService<ISemanticTextMemory>())
                .Build());

        return services;
    }

    /// <summary>
    /// Add the completion backend to the kernel config
    /// </summary>
    private static KernelBuilder WithCompletionBackend(this KernelBuilder kernelBuilder, AIServiceOptions aiServiceOptions)
    {
        switch (aiServiceOptions.AIService)
        {
            case AIServiceOptions.AIServiceType.AzureOpenAI:
                kernelBuilder.WithAzureChatCompletionService(
                    deploymentName: aiServiceOptions.DeploymentOrModelId,
                    endpoint: aiServiceOptions.Endpoint,
                    apiKey: aiServiceOptions.Key);
                break;

            case AIServiceOptions.AIServiceType.OpenAI:
                kernelBuilder.WithOpenAIChatCompletionService(
                   modelId: aiServiceOptions.DeploymentOrModelId,
                   apiKey: aiServiceOptions.Key);
                break;

            default:
                throw new ArgumentException($"Invalid {nameof(aiServiceOptions.AIService)} value in '{AIServiceOptions.CompletionPropertyName}' settings.");
        }

        return kernelBuilder;
    }

    /// <summary>
    /// Add the embedding backend to the kernel config
    /// </summary>
    private static KernelBuilder WithEmbeddingBackend(this KernelBuilder kernelBuilder, AIServiceOptions aiServiceOptions)
    {
        switch (aiServiceOptions.AIService)
        {
            case AIServiceOptions.AIServiceType.AzureOpenAI:
                kernelBuilder.WithAzureTextEmbeddingGenerationService(
                    deploymentName: aiServiceOptions.DeploymentOrModelId,
                    endpoint: aiServiceOptions.Endpoint,
                    apiKey: aiServiceOptions.Key,
                    serviceId: aiServiceOptions.Label);
                break;

            case AIServiceOptions.AIServiceType.OpenAI:
                kernelBuilder.WithOpenAITextEmbeddingGenerationService(
                    modelId: aiServiceOptions.DeploymentOrModelId,
                    apiKey: aiServiceOptions.Key,
                    serviceId: aiServiceOptions.Label);
                break;

            default:
                throw new ArgumentException($"Invalid {nameof(aiServiceOptions.AIService)} value in '{AIServiceOptions.EmbeddingPropertyName}' settings.");
        }

        return kernelBuilder;
    }

    /// <summary>
    /// Construct IEmbeddingGeneration from <see cref="AIServiceOptions"/>
    /// </summary>
    /// <param name="serviceConfig">The service configuration</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    private static ITextEmbeddingGeneration ToTextEmbeddingsService(this AIServiceOptions serviceConfig,
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
