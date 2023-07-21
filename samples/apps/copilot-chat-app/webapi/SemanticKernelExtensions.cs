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
using Microsoft.SemanticKernel.Connectors.Memory.AzureSearch;
using Microsoft.SemanticKernel.Connectors.Memory.Qdrant;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Skills.Core;
using Microsoft.SemanticKernel.TemplateEngine;
using SemanticKernel.Service.CopilotChat.Extensions;
using SemanticKernel.Service.CopilotChat.Storage;
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
                .WithCompletionBackend(sp.GetRequiredService<IOptions<AIServiceOptions>>().Value)
                .WithEmbeddingBackend(sp.GetRequiredService<IOptions<AIServiceOptions>>().Value)
                .Build();

            sp.GetRequiredService<RegisterSkillsWithKernel>()(sp, kernel);
            return kernel;
        });

        // Semantic memory
        services.AddSemanticTextMemory();

        // Register skills
        services.AddScoped<RegisterSkillsWithKernel>(sp => RegisterSkillsAsync);

        return services;
    }

    /// <summary>
    /// Register the skills with the kernel.
    /// </summary>
    private static Task RegisterSkillsAsync(IServiceProvider sp, IKernel kernel)
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
                    sp.GetRequiredService<IOptions<AIServiceOptions>>().Value
                        .ToTextEmbeddingsService(logger: sp.GetRequiredService<ILogger<AIServiceOptions>>())));
                break;

            case MemoriesStoreOptions.MemoriesStoreType.Qdrant:
                if (config.Qdrant == null)
                {
                    throw new InvalidOperationException("MemoriesStore type is Qdrant and Qdrant configuration is null.");
                }

                services.AddSingleton<IMemoryStore>(sp =>
                {
                    HttpClient httpClient = new(new HttpClientHandler { CheckCertificateRevocationList = true });
                    if (!string.IsNullOrWhiteSpace(config.Qdrant.Key))
                    {
                        httpClient.DefaultRequestHeaders.Add("api-key", config.Qdrant.Key);
                    }

                    var endPointBuilder = new UriBuilder(config.Qdrant.Host);
                    endPointBuilder.Port = config.Qdrant.Port;

                    return new QdrantMemoryStore(
                        httpClient: httpClient,
                        config.Qdrant.VectorSize,
                        endPointBuilder.ToString(),
                        logger: sp.GetRequiredService<ILogger<IQdrantVectorDbClient>>()
                    );
                });
                services.AddScoped<ISemanticTextMemory>(sp => new SemanticTextMemory(
                    sp.GetRequiredService<IMemoryStore>(),
                    sp.GetRequiredService<IOptions<AIServiceOptions>>().Value
                        .ToTextEmbeddingsService(logger: sp.GetRequiredService<ILogger<AIServiceOptions>>())));
                break;

            case MemoriesStoreOptions.MemoriesStoreType.AzureCognitiveSearch:
                if (config.AzureCognitiveSearch == null)
                {
                    throw new InvalidOperationException("MemoriesStore type is AzureCognitiveSearch and AzureCognitiveSearch configuration is null.");
                }

                // ACS's vector search where users provide their embeddings
                if (config.AzureCognitiveSearch.UseVectorSearch)
                {
                    services.AddSingleton<IMemoryStore>(sp =>
                    {
                        return new AzureSearchMemoryStore(config.AzureCognitiveSearch.Endpoint, config.AzureCognitiveSearch.Key);
                    });
                    services.AddScoped<ISemanticTextMemory>(sp => new SemanticTextMemory(
                        sp.GetRequiredService<IMemoryStore>(),
                        sp.GetRequiredService<IOptions<AIServiceOptions>>().Value
                            .ToTextEmbeddingsService(logger: sp.GetRequiredService<ILogger<AIServiceOptions>>())));
                }
                // ACS's semantic search where ACS calculates the embeddings
                else
                {
                    services.AddSingleton<ISemanticTextMemory>(sp => new AzureCognitiveSearchMemory(config.AzureCognitiveSearch.Endpoint, config.AzureCognitiveSearch.Key));
                }
                break;

            default:
                throw new InvalidOperationException($"Invalid 'MemoriesStore' type '{config.Type}'.");
        }

        // High level semantic memory implementations, such as Azure Cognitive Search's Semantic Search, do not allow for providing embeddings when storing memories.
        // We wrap the memory store in an optional memory store to allow controllers to pass dependency injection validation and potentially optimize
        // for a lower-level memory implementation (e.g. Qdrant). Lower level memory implementations (i.e., IMemoryStore) allow for reusing embeddings,
        // whereas high level memory implementation (i.e., ISemanticTextMemory) assume embeddings get recalculated on every write.
        services.AddSingleton<OptionalIMemoryStore>(sp => new OptionalIMemoryStore() { MemoryStore = sp.GetService<IMemoryStore>() });
    }

    /// <summary>
    /// Add the completion backend to the kernel config
    /// </summary>
    private static KernelBuilder WithCompletionBackend(this KernelBuilder kernelBuilder, AIServiceOptions options)
    {
        return options.Type switch
        {
            AIServiceOptions.AIServiceType.AzureOpenAI
                => kernelBuilder.WithAzureChatCompletionService(options.Models.Completion, options.Endpoint, options.Key),
            AIServiceOptions.AIServiceType.OpenAI
                => kernelBuilder.WithOpenAIChatCompletionService(options.Models.Completion, options.Key),
            _
                => throw new ArgumentException($"Invalid {nameof(options.Type)} value in '{AIServiceOptions.PropertyName}' settings."),
        };
    }

    /// <summary>
    /// Add the embedding backend to the kernel config
    /// </summary>
    private static KernelBuilder WithEmbeddingBackend(this KernelBuilder kernelBuilder, AIServiceOptions options)
    {
        return options.Type switch
        {
            AIServiceOptions.AIServiceType.AzureOpenAI
                => kernelBuilder.WithAzureTextEmbeddingGenerationService(options.Models.Embedding, options.Endpoint, options.Key),
            AIServiceOptions.AIServiceType.OpenAI
                => kernelBuilder.WithOpenAITextEmbeddingGenerationService(options.Models.Embedding, options.Key),
            _
                => throw new ArgumentException($"Invalid {nameof(options.Type)} value in '{AIServiceOptions.PropertyName}' settings."),
        };
    }

    /// <summary>
    /// Construct IEmbeddingGeneration from <see cref="AIServiceOptions"/>
    /// </summary>
    /// <param name="options">The service configuration</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">Application logger</param>
    private static ITextEmbeddingGeneration ToTextEmbeddingsService(this AIServiceOptions options,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        return options.Type switch
        {
            AIServiceOptions.AIServiceType.AzureOpenAI
                => new AzureTextEmbeddingGeneration(options.Models.Embedding, options.Endpoint, options.Key, httpClient: httpClient, logger: logger),
            AIServiceOptions.AIServiceType.OpenAI
                => new OpenAITextEmbeddingGeneration(options.Models.Embedding, options.Key, httpClient: httpClient, logger: logger),
            _
                => throw new ArgumentException("Invalid AIService value in embeddings backend settings"),
        };
    }
}
