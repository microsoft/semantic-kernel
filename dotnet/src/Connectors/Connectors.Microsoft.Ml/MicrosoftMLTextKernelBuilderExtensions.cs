using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel;


#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

public static class MsMLTextKernelBuilderExtensions
{
    /// <param name="vocabFile">The JSON file path containing the dictionary of string keys and their ids.</param>
    /// <param name="mergesFile">The file path containing the tokens's pairs list.</param>
    public static KernelBuilder WithMsMLTextTextEmbeddingGenerationService(this KernelBuilder builder,
        string mergeFilePath = @"merges.txt",
        string vocabFilePath = @"vocab.json",
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        builder.WithAIService<ITextEmbeddingGeneration>(serviceId, (loggerFactory) =>
            new MsTextEmbeddingGeneration(
                loggerFactory: loggerFactory,
                mergeFilePath: mergeFilePath,
                vocabFilePath: vocabFilePath
                ),
                setAsDefault);

        return builder;
    }
}


