// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure.AI.OpenAI;
using Microsoft.Extensions.AI;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <inheritdoc />
public sealed class AzureOpenAIEmbeddingGeneratorMetadata : EmbeddingGeneratorMetadata
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIEmbeddingGeneratorMetadata"/> class.
    /// </summary>
    public AzureOpenAIEmbeddingGeneratorMetadata(string deploymentName, string providerName, string defaultModelId, Uri? providerUri, int? defaultModelDimensions = null, string? apiVersion = null)
        : base(providerName, providerUri, defaultModelId, defaultModelDimensions)
    {
        this.DeploymentName = deploymentName;
        this.ApiVersion = apiVersion;
    }

    /// <summary>Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource.</summary>
    public string DeploymentName { get; }

    /// <summary>Optional Azure OpenAI API version, see available here <see cref="AzureOpenAIClientOptions.ServiceVersion"/>.</summary>
    public string? ApiVersion { get; }
}
