// Copyright (c) Microsoft. All rights reserved.

using System;
using Amazon.BedrockRuntime;
using Amazon.Runtime;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding Bedrock modality services to the service collection.
/// </summary>
public static class BedrockServiceCollectionExtensions
{
    /// <summary>
    /// Add Amazon Bedrock Chat Completion service to the <see cref="IServiceCollection" />.
    /// </summary>
    /// <param name="service">The service collection.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="bedrockRuntime">The optional <see cref="IAmazonBedrockRuntime" /> to use. If not provided will be retrieved from the Service Collection.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>Returns back <see cref="IServiceCollection"/> with a configured service.</returns>
    public static IServiceCollection AddBedrockChatCompletionService(
        this IServiceCollection service,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null)
    {
        Verify.NotNull(service);

        if (bedrockRuntime == null)
        {
            // Add IAmazonBedrockRuntime service client to the DI container
            service.TryAddAWSService<IAmazonBedrockRuntime>();
        }

        service.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
        {
            try
            {
                IAmazonBedrockRuntime runtime = bedrockRuntime ?? serviceProvider.GetRequiredService<IAmazonBedrockRuntime>();
                var logger = serviceProvider.GetService<ILoggerFactory>();
                // Check if the runtime instance is a proxy object
                if (runtime.GetType().BaseType == typeof(AmazonServiceClient))
                {
                    // Cast to AmazonServiceClient and subscribe to the event
                    ((AmazonServiceClient)runtime).BeforeRequestEvent += BedrockClientUtilities.BedrockServiceClientRequestHandler;
                }
                return new BedrockChatCompletionService(modelId, runtime, logger);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the {nameof(BedrockChatCompletionService)}: {ex.Message}", ex);
            }
        });

        return service;
    }

    /// <summary>
    /// Add Amazon Bedrock Text Generation service to the <see cref="IServiceCollection" />.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bedrockRuntime">The optional <see cref="IAmazonBedrockRuntime" /> to use. If not provided will be retrieved from the Service Collection.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>Returns back <see cref="IServiceCollection"/> with a configured service.</returns>
    public static IServiceCollection AddBedrockTextGenerationService(
        this IServiceCollection services,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null)
    {
        if (bedrockRuntime == null)
        {
            // Add IAmazonBedrockRuntime service client to the DI container
            services.TryAddAWSService<IAmazonBedrockRuntime>();
        }
        services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
        {
            try
            {
                IAmazonBedrockRuntime runtime = bedrockRuntime ?? serviceProvider.GetRequiredService<IAmazonBedrockRuntime>();
                var logger = serviceProvider.GetService<ILoggerFactory>();
                // Check if the runtime instance is a proxy object
                if (runtime.GetType().BaseType == typeof(AmazonServiceClient))
                {
                    // Cast to AmazonServiceClient and subscribe to the event
                    ((AmazonServiceClient)runtime).BeforeRequestEvent += BedrockClientUtilities.BedrockServiceClientRequestHandler;
                }
                return new BedrockTextGenerationService(modelId, runtime, logger);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the {nameof(BedrockTextGenerationService)}: {ex.Message}", ex);
            }
        });

        return services;
    }

    /// <summary>
    /// Add Amazon Bedrock Text Generation service to the <see cref="IServiceCollection" />.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bedrockRuntime">The optional <see cref="IAmazonBedrockRuntime" /> to use. If not provided will be retrieved from the Service Collection.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>Returns back <see cref="IServiceCollection"/> with a configured service.</returns>
    public static IServiceCollection AddBedrockTextEmbeddingGenerationService(
        this IServiceCollection services,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null)
    {
        if (bedrockRuntime == null)
        {
            // Add IAmazonBedrockRuntime service client to the DI container
            services.TryAddAWSService<IAmazonBedrockRuntime>();
        }
        services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
        {
            try
            {
                IAmazonBedrockRuntime runtime = bedrockRuntime ?? serviceProvider.GetRequiredService<IAmazonBedrockRuntime>();
                var logger = serviceProvider.GetService<ILoggerFactory>();
                // Check if the runtime instance is a proxy object
                if (runtime.GetType().BaseType == typeof(AmazonServiceClient))
                {
                    // Cast to AmazonServiceClient and subscribe to the event
                    ((AmazonServiceClient)runtime).BeforeRequestEvent += BedrockClientUtilities.BedrockServiceClientRequestHandler;
                }
                return new BedrockTextEmbeddingGenerationService(modelId, runtime, logger);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the {nameof(BedrockTextEmbeddingGenerationService)}: {ex.Message}", ex);
            }
        });

        return services;
    }
}
