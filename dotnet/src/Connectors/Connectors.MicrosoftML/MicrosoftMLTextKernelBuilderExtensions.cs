// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.Embeddings;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Extensions for configuring MsMLTextKernelBuilder.
/// </summary>
public static class MsMLTextKernelBuilderExtensions
{
    /// <summary>
    /// Configures the MsMLTextTextEmbeddingGenerationService for text embedding generation.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <param name="vocabFilePath">The JSON file path containing the dictionary of string keys and their ids.</param>
    /// <param name="mergeFilePath">The file path containing the tokens's pairs list.</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    public static KernelBuilder WithMicrosoftMLTextTextEmbeddingGenerationService(this KernelBuilder builder,
        string? serviceId = null,
        string vocabFilePath = "vocab.json",
        string mergeFilePath = "merges.txt",
        bool setAsDefault = false)
    {
        builder.WithAIService<ITextEmbeddingGeneration>(serviceId, (loggerFactory) =>
            new MicrosoftMLTextEmbeddingGeneration(
                loggerFactory: loggerFactory,
                mergeFilePath: mergeFilePath,
                vocabFilePath: vocabFilePath
                ),
                setAsDefault);

        return builder;
    }
}
