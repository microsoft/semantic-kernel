// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Connectors.Amazon.Services;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Services;
using Microsoft.SemanticKernel.TextGeneration;

namespace Connectors.Amazon.Extensions;

/// <summary>
/// Extensions for adding Bedrock services to the application.
/// </summary>
public static class BedrockKernelBuilderExtensions
{
    /// <summary>
    /// Add Amazon Bedrock Chat Completion service to the kernel builder using IAmazonBedrockRuntime object.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="bedrockRuntime">The IAmazonBedrockRuntime to run inference using the respective model.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns></returns>
    public static IKernelBuilder AddBedrockChatCompletionService(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null)
    {
        if (bedrockRuntime == null)
        {
            // Add IAmazonBedrockRuntime service client to the DI container
            builder.Services.TryAddAWSService<IAmazonBedrockRuntime>();
        }

        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
        {
            try
            {
                IAmazonBedrockRuntime runtime = bedrockRuntime ?? serviceProvider.GetRequiredService<IAmazonBedrockRuntime>();
                var logger = serviceProvider.GetService<ILoggerFactory>();
                return new BedrockChatCompletionService(modelId, runtime, logger);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the {nameof(BedrockChatCompletionService)}: {ex.Message}", ex);
            }
        });

        return builder;
    }

    /// <summary>
    /// Add Amazon Bedrock Text Generation service to the kernel builder using IAmazonBedrockRuntime object.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bedrockRuntime">The IAmazonBedrockRuntime to run inference using the respective model.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns></returns>
    public static IKernelBuilder AddBedrockTextGenerationService(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null)
    {
        if (bedrockRuntime == null)
        {
            // Add IAmazonBedrockRuntime service client to the DI container
            builder.Services.TryAddAWSService<IAmazonBedrockRuntime>();
        }
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
        {
            try
            {
                IAmazonBedrockRuntime runtime = bedrockRuntime ?? serviceProvider.GetRequiredService<IAmazonBedrockRuntime>();
                var logger = serviceProvider.GetService<ILoggerFactory>();
                return new BedrockTextGenerationService(modelId, runtime, logger);
            }
            catch (Exception ex)
            {
                throw new KernelException($"An error occurred while initializing the {nameof(BedrockTextGenerationService)}: {ex.Message}", ex);
            }
        });

        return builder;
    }
}
