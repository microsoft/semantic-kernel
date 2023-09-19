// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
#pragma warning disable IDE0005
using Microsoft.ML.Tokenizers;
#pragma warning restore IDE0005

using Microsoft.SemanticKernel.AI.Embeddings;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130
/// <summary>
/// Provides text embedding generation using a BPE tokenizer.
/// </summary>
public sealed class MicrosoftMLTextEmbeddingGeneration : ITextEmbeddingGeneration
{
    private string vocabFilePath;
    private string mergeFilePath;
    private Tokenizer tokenizer;
    /// <summary>
    /// Gets the logger instance.
    /// </summary>
    private ILogger Logger { get; set; }

    /// <summary>
    /// Initializes a new instance of the MicrosoftMLTextEmbeddingGeneration class.
    /// </summary>
    /// <param name="vocabFile">The JSON file path containing the dictionary of string keys and their ids.</param>
    /// <param name="mergesFile">The file path containing the tokens's pairs list.</param>
    /// <param name="loggerFactory">Optional logger factory for logging.</param>
    public MicrosoftMLTextEmbeddingGeneration(
        string mergeFilePath,
        string vocabFilePath,
        ILoggerFactory? loggerFactory = null
    )
    {
        this.vocabFilePath = vocabFilePath;
        this.mergeFilePath = mergeFilePath;
        this.tokenizer = new Tokenizer(new Bpe(vocabFilePath, mergeFilePath));
        this.Logger = loggerFactory is not null ? loggerFactory.CreateLogger(this.GetType()) : NullLogger.Instance;
    }

    /// <summary>
    /// Generates embeddings asynchronously for a list of input texts.
    /// </summary>
    /// <param name="data">The list of input texts to generate embeddings for.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>A task that represents the asynchronous operation and returns a list of embeddings.</returns>
    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, CancellationToken cancellationToken = default)
    {
        var result = new List<ReadOnlyMemory<float>>(data.Count);
        foreach (string text in data)
        {
            var embeddings = GenerateEmbeddingsFromTokens(this.tokenizer.Encode(text), cancellationToken);

            // Add the embeddings to the result list
            result.Add(embeddings);
        }

        return Task.FromResult<IList<ReadOnlyMemory<float>>>(result);
    }

    /// <summary>
    /// Generates embeddings from tokenizer tokens.
    /// </summary>
    /// <param name="token">The tokenizer result.</param>
    /// <param name="cancellationToken">Optional cancellation token.</param>
    /// <returns>A ReadOnlyMemory of float representing the embeddings.</returns>
    private static ReadOnlyMemory<float> GenerateEmbeddingsFromTokens(TokenizerResult token, CancellationToken cancellationToken)
    {
        // Convert token.Ids (int) to float
        var floatIds = token.Ids.Select(id => (float)id).ToArray();

        // Create a ReadOnlyMemory<float> from the floatIds array
        var embeddings = new ReadOnlyMemory<float>(floatIds);

        return embeddings;
    }
}
