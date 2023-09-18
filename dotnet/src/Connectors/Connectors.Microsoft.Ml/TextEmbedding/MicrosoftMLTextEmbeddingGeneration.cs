using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.ML.Tokenizers;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130
public sealed class MsTextEmbeddingGeneration : ITextEmbeddingGeneration
{
    private string vocabFilePath;
    private string mergeFilePath;
    private Tokenizer tokenizer;
    /// <summary>
    /// Logger instance
    /// </summary>
    private ILogger Logger { get; set; }

    /// <summary>
    /// Construct a new Bpe model object to use for sentence tokenization and tokenizer training.
    /// </summary>
    /// <param name="vocabFile">The JSON file path containing the dictionary of string keys and their ids.</param>
    /// <param name="mergesFile">The file path containing the tokens's pairs list.</param>
    public MsTextEmbeddingGeneration(
        string mergeFilePath = @"merges.txt",
        string vocabFilePath = @"vocab.json",
        ILoggerFactory? loggerFactory = null
    ) : base()
    {
        this.vocabFilePath = vocabFilePath;
        this.mergeFilePath = mergeFilePath;
        this.tokenizer = new Tokenizer(new Bpe(vocabFilePath, mergeFilePath));
        this.Logger = loggerFactory is not null ? loggerFactory.CreateLogger(this.GetType()) : NullLogger.Instance;
    }

    public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, CancellationToken cancellationToken = default)
    {
        var result = new List<ReadOnlyMemory<float>>(data.Count);
        foreach (string text in data)
        {

            var tokenizerEncodedResult = tokenizer.Encode(text);
            var embeddings = GenerateEmbeddingsFromTokens(tokenizerEncodedResult, cancellationToken);

            // Add the embeddings to the result list
            result.Add(embeddings);

        }

        return Task.FromResult<IList<ReadOnlyMemory<float>>>(result);
    }
    private static ReadOnlyMemory<float> GenerateEmbeddingsFromTokens(TokenizerResult token, CancellationToken cancellationToken)
    {
        // Convert token.Ids (int) to float
        var floatIds = token.Ids.Select(id => (float)id).ToArray();

        // Create a ReadOnlyMemory<float> from the floatIds array
        var embeddings = new ReadOnlyMemory<float>(floatIds);

        return embeddings;

    }


}
