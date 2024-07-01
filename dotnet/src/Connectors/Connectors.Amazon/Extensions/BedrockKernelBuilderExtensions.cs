// Copyright (c) Microsoft. All rights reserved.
using Amazon.BedrockRuntime;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Connectors.Amazon.Models;
using Connectors.Amazon.Services;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Extensions;

public static class BedrockKernelBuilderExtensions
{
    public static IKernelBuilder AddBedrockChatGenerationService(
        this IKernelBuilder builder,
        string modelId,
        IAmazonBedrockRuntime bedrockApi,
        IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse> ioService,
        string? serviceId = null)
    {
        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _)
            => new BedrockChatCompletionService(modelId, bedrockApi, ioService));

        return builder;
    }

    public static IKernelBuilder AddBedrockChatGenerationService(
        this IKernelBuilder builder,
        string modelId,
        IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse> ioService,
        string? serviceId = null)
    {
        builder.Services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _)
            => new BedrockChatCompletionService(modelId, ioService));

        return builder;
    }
}
