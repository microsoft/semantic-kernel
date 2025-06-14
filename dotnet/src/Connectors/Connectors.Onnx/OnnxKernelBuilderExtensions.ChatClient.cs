// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel;

/// <summary>Extension methods for <see cref="IKernelBuilder"/>.</summary>
[Experimental("SKEXP0010")]
public static class OnnxChatClientKernelBuilderExtensions
{
    #region Chat Client

    /// <summary>
    /// Adds an OnnxRuntimeGenAI <see cref="IChatClient"/> to the <see cref="IKernelBuilder.Services"/>.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="modelId">Model Id.</param>
    /// <param name="modelPath">The generative AI ONNX model path.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddOnnxRuntimeGenAIChatClient(
        this IKernelBuilder builder,
        string modelId,
        string modelPath,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddOnnxRuntimeGenAIChatClient(
            modelId,
            modelPath,
            serviceId);

        return builder;
    }

    #endregion
}
