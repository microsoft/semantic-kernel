// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI client specialized chat completion options.
/// </summary>
public class OpenAITextEmbeddingGenerationConfig : BaseServiceConfig
{
    /// <summary>
    /// The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; init; }

    /// <summary>
    /// The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.
    /// </summary>
    public int? Dimensions { get; init; }
}
