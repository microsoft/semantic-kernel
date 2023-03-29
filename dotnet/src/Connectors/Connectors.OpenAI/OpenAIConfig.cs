// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI configuration.
/// </summary>
public sealed class OpenAIConfig : ServiceConfig
{
    /// <summary>
    /// OpenAI model name, see https://platform.openai.com/docs/models
    /// </summary>
    public string ModelId { get; }

    /// <summary>
    /// OpenAI API key, see https://platform.openai.com/account/api-keys
    /// </summary>
    public string APIKey { get; }

    /// <summary>
    /// OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.
    /// </summary>
    public string? OrgId { get; }

    /// <summary>
    /// Creates a new <see cref="OpenAIConfig" /> with supplied values.
    /// </summary>
    /// <param name="serviceId">An identifier used to map semantic functions to AI services and models,
    /// decoupling prompts configurations from the actual model used.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    public OpenAIConfig(string serviceId, string modelId, string apiKey, string? orgId)
        : base(serviceId)
    {
        Verify.NotEmpty(modelId, "The model ID is empty");
        Verify.NotEmpty(apiKey, "The API key is empty");

        this.ModelId = modelId;
        this.APIKey = apiKey;
        this.OrgId = orgId;
    }
}
