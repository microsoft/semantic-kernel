// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.ML.OnnxRuntimeGenAI;
using Microsoft.SemanticKernel.Connectors.Onnx;

namespace Microsoft.SemanticKernel;

/// <summary>Extension methods for <see cref="IKernelBuilder"/>.</summary>
public static class OnnxChatClientKernelBuilderExtensions
{
    #region Chat Client

    /// <summary>
    /// Adds an OnnxRuntimeGenAI <see cref="IChatClient"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelPath">The generative AI ONNX model path.</param>
    /// <param name="chatClientOptions">The optional options for the chat client.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddOnnxRuntimeGenAIChatClient(
        this IKernelBuilder builder,
        string modelPath,
        OnnxRuntimeGenAIChatClientOptions? chatClientOptions = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddOnnxRuntimeGenAIChatClient(
            modelPath,
            chatClientOptions,
            serviceId);

        return builder;
    }

    /// <summary>
    /// Adds an OnnxRuntimeGenAI <see cref="IChatClient"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelPath">The generative AI ONNX model path.</param>
    /// <param name="providers">The providers to use for the chat client.</param>
    /// <param name="chatClientOptions">The optional options for the chat client.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddOnnxRuntimeGenAIChatClient(
        this IKernelBuilder builder,
        string modelPath,
        IEnumerable<Provider> providers,
        OnnxRuntimeGenAIChatClientOptions? chatClientOptions = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddOnnxRuntimeGenAIChatClient(
            modelPath,
            providers,
            chatClientOptions,
            serviceId);

        return builder;
    }
    #endregion
}
