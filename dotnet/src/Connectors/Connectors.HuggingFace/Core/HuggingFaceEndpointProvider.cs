// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

internal sealed class HuggingFaceEndpointProvider : IEndpointProvider
{
    private readonly Uri? _endPoint;
    private readonly string _separator;

    /// <summary>
    /// Initializes a new instance of the HuggingFace Endpoints class with the specified API key.
    /// </summary>
    /// <param name="endPoint">Endpoint url for Hugging Face Inference API</param>
    public HuggingFaceEndpointProvider(Uri? endPoint)
    {
        if (endPoint is null)
        {
            endPoint = new Uri("https://api-inference.huggingface.co");
        }

        this._separator = endPoint.AbsolutePath.EndsWith("/", StringComparison.InvariantCulture) ? string.Empty : "/";
        this._endPoint = endPoint;
    }

    /// <summary>
    /// Initializes a new instance of the HuggingFace Endpoints class with the public API endpoint.
    /// </summary>
    /// <remarks>
    /// Public API endpoint: https://api-inference.huggingface.co
    /// </remarks>
    public HuggingFaceEndpointProvider() : this(null)
    {
    }

    public Uri GetTextGenerationEndpoint(string modelId)
        => new($"{this._endPoint}{this._separator}models/{modelId}");

    public Uri GetEmbeddingGenerationEndpoint(string modelId)
        => new($"{this._endPoint}{this._separator}pipeline/feature-extraction/{modelId}");
}
