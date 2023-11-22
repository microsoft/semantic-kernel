// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.Ollama.TextCompletion;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure Ollama connectors.
/// </summary>
public static class OllamaKernelBuilderExtensions
{
    /// <summary>
    /// Adds IKernel with a configured LLM to Semantic Kernel
    /// </summary>
    /// <param name="builder">kernle builder</param>
    /// <param name="modelId">Ollama model ID to use</param>
    /// <param name="baseUrl">Ollama base url</param>
    /// <param name="serviceId"></param>
    /// <returns></returns>
    public static KernelBuilder WithOllamaTextCompletionService(
        this KernelBuilder builder,
        string modelId,
        string baseUrl,
        string? serviceId = null
    )
    {
        builder.WithAIService<ITextCompletion>(serviceId, loggerFactory =>
        {
            return new OllamaTextCompletion(modelId, baseUrl, loggerFactory);
        });

        return builder;
    }

    /// <summary>
    /// Adds IKernel with a configured LLM to Semantic Kernel
    /// </summary>
    /// <param name="builder">kernel builder</param>
    /// <param name="modelId">Ollama model ID to use</param>
    /// <param name="baseUrl">Ollama base url</param>
    /// <param name="serviceId"></param>
    /// <returns></returns>
    public static KernelBuilder WithOllamaTextCompletionService(this KernelBuilder builder, string modelId, System.Uri baseUrl, string? serviceId = null)
    {
        builder.WithAIService<ITextCompletion>(serviceId, loggerFactory =>
        {
            return new OllamaTextCompletion(modelId, baseUrl.AbsoluteUri, loggerFactory);
        });

        return builder;
    }
}
