// Copyright (c) Microsoft. All rights reserved.

namespace Connectors.Amazon.Core.Responses;

/// <summary>
/// Text generation response object. Variation too high between different models. Each model will just address their own response parameter requirements.
/// </summary>
public interface ITextGenerationResponse
{
    /// <summary>
    /// Number of tokens in the response.
    /// </summary>
    public int TokenCount { get; set; }
}
