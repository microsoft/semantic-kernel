// Copyright (c) Microsoft. All rights reserved.

using System;
using Amazon.BedrockRuntime;
using Amazon.Runtime;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding Bedrock services to the application.
/// </summary>
public static class BedrockServiceCollectionExtensions
{
    /// <summary>
    /// Add Amazon Bedrock Chat Completion service to the kernel builder using IAmazonBedrockRuntime object.
    /// </summary>
    /// <param name="service">The kernel builder.</param>
    /// <param name="modelId">The model for chat completion.</param>
    /// <param name="bedrockRuntime">The IAmazonBedrockRuntime to run inference using the respective model.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns><see cref="IKernelBuilder"/> object.</returns>
    public static IServiceCollection AddBedrockChatCompletionService(
        this IServiceCollection service,
        string modelId,
        IAmazonBedrockRuntime? bedrockRuntime = null,
        string? serviceId = null)
    {
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
                    ((AmazonServiceClient)runtime).BeforeRequestEvent += AWSServiceClient_BeforeServiceRequest;
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
    /// Add Amazon Bedrock Text Generation service to the kernel builder using IAmazonBedrockRuntime object.
    /// </summary>
    /// <param name="services">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bedrockRuntime">The IAmazonBedrockRuntime to run inference using the respective model.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns><see cref="IKernelBuilder"/> object.</returns>
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
                    ((AmazonServiceClient)runtime).BeforeRequestEvent += AWSServiceClient_BeforeServiceRequest;
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

    internal static void AWSServiceClient_BeforeServiceRequest(object sender, RequestEventArgs e)
    {
        if (e is not WebServiceRequestEventArgs args || !args.Headers.TryGetValue(BedrockClientUtilities.UserAgentHeader, out string? value) || value.Contains(BedrockClientUtilities.UserAgentString))
        {
            return;
        }
        args.Headers[BedrockClientUtilities.UserAgentHeader] = $"{value} {BedrockClientUtilities.UserAgentString}";
    }
}
