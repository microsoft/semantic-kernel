// Copyright (c) Microsoft. All rights reserved.
using Amazon.BedrockRuntime;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;
using Connectors.Amazon.Services;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.TextGeneration;

namespace Connectors.Amazon.Extensions;

public static class BedrockKernelBuilderExtensions
{
    public static IKernelBuilder AddBedrockChatCompletionService(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime bedrockApi,
        string? serviceId = null)
    {
        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _)
            => new BedrockChatCompletionService(modelId, bedrockApi));

        return builder;
    }

    public static IKernelBuilder AddBedrockChatCompletionService(
        this IKernelBuilder builder,
        string modelId,
        string? serviceId = null)
    {
        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _)
            => new BedrockChatCompletionService(modelId));

        return builder;
    }

    public static IKernelBuilder AddBedrockTextGenerationService(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime bedrockApi,
        string? serviceId = null)
    {
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _)
            => new BedrockTextGenerationService(modelId, bedrockApi));

        return builder;
    }

    public static IKernelBuilder AddBedrockTextGenerationService(
        this IKernelBuilder builder,
        string modelId,
        string? serviceId = null)
    {
        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _)
            => new BedrockTextGenerationService(modelId));

        return builder;
    }
}
