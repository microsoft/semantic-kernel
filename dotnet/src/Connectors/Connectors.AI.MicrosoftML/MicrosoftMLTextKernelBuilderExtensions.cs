// Copyright (c) Microsoft. All rights reserved.

using Microsoft.ML.Tokenizers;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.AI.MicrosoftML.TextEmbedding;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure Microsoft.ML embeddings connectors.
/// </summary>
public static class MicrosoftMLTextKernelBuilderExtensions
{
    /// <summary>
    /// Configures the MicrosoftMLTextEmbeddingGenerationService for text embedding generation.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="vocabFilePath">The JSON file path containing the dictionary of string keys and their ids.</param>
    /// <param name="mergeFilePath">The file path containing the tokens's pairs list.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <returns>The modified <see cref="KernelBuilder"/> instance.</returns>
    public static KernelBuilder WithMicrosoftMLTextEmbeddingGenerationService(this KernelBuilder builder,
        string vocabFilePath = "vocab.json",
        string mergeFilePath = "merges.txt",
        string? serviceId = null,
        bool setAsDefault = false)
    {
        builder.WithAIService<ITextEmbeddingGeneration>(
            serviceId,
            (loggerFactory) =>
                new MicrosoftMLTextEmbeddingGeneration(
                    loggerFactory: loggerFactory,
                    mergeFilePath: mergeFilePath,
                    vocabFilePath: vocabFilePath
                ),
            setAsDefault);

        return builder;
    }

    /// <summary>
    /// Configures the MicrosoftMLTextEmbeddingGenerationService for text embedding generation.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="tokenizer">The tokenizer to use for tokenization and embeddings generation.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <param name="setAsDefault">Whether the service should be the default for its type.</param>
    /// <returns>The modified <see cref="KernelBuilder"/> instance.</returns>
    public static KernelBuilder WithMicrosoftMLTextEmbeddingGenerationService(this KernelBuilder builder,
        Tokenizer tokenizer,
        string? serviceId = null,
        bool setAsDefault = false)
    {
        builder.WithAIService<ITextEmbeddingGeneration>(
            serviceId,
            (loggerFactory) => new MicrosoftMLTextEmbeddingGeneration(tokenizer),
            setAsDefault);

        return builder;
    }
}
