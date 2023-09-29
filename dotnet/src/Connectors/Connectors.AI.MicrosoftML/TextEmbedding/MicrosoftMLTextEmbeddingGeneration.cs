// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.ML.Tokenizers;
using Microsoft.SemanticKernel.AI.Embeddings;

namespace Microsoft.SemanticKernel.Connectors.AI.MicrosoftML.TextEmbedding;

/// <summary>
/// Provides text embedding generation using a BPE or custom tokenizer.
/// </summary>
public sealed class MicrosoftMLTextEmbeddingGeneration : ITextEmbeddingGeneration
{
    private readonly Tokenizer _tokenizer;

    /// <summary>
    /// Gets the logger instance.
    /// </summary>
    private ILogger Logger { get; set; }

    /// <summary>
    /// Initializes a new instance of the MicrosoftMLTextEmbeddingGeneration class using the default Bpe tokenizer.
    /// </summary>
    /// <param name="vocabFilePath">The JSON file path containing the dictionary of string keys and their ids.</param>
    /// <param name="mergeFilePath">The file path containing the tokens's pairs list.</param>
    /// <param name="loggerFactory">Optional logger factory for logging.</param>
    public MicrosoftMLTextEmbeddingGeneration(
        string vocabFilePath,
        string mergeFilePath,
        ILoggerFactory? loggerFactory = null
    )
    {
        this._tokenizer = new Tokenizer(new Bpe(vocabFilePath, mergeFilePath));
        this.Logger = loggerFactory is not null ? loggerFactory.CreateLogger(this.GetType()) : NullLogger.Instance;
    }

    /// <summary>
    /// Initializes a new instance of the MicrosoftMLTextEmbeddingGeneration class using a custom tokenizer.
    /// </summary>
    /// <param name="tokenizer">The tokenizer to use for tokenization and embeddings generation.</param>
    /// <param name="loggerFactory">Optional logger factory for logging.</param>
    public MicrosoftMLTextEmbeddingGeneration(
        Tokenizer tokenizer,
        ILoggerFactory? loggerFactory = null
    )
    {
        this._tokenizer = tokenizer;
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
            var embeddings = GenerateEmbeddingsFromTokens(this._tokenizer.Encode(text), cancellationToken);

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
