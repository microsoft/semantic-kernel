// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

internal sealed class HuggingFaceEndpointProvider : IEndpointProvider
{
    /// <summary>
    /// Initializes a new instance of the HuggingFace Endpoints class with the specified API key.
    /// </summary>
    /// <param name="baseUri">Base url for Hugging Face Inference API</param>
    public HuggingFaceEndpointProvider(Uri baseUri)
    {
        this.TextGenerationEndpoint = new Uri($"{baseUri}models/");
    }

    public HuggingFaceEndpointProvider() : this(new Uri("https://api-inference.huggingface.co/"))
    {
    }

    public Uri TextGenerationEndpoint { get; }
}
