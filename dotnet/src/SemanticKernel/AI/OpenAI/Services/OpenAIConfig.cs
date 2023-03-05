// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Configuration;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;

/// <summary>
/// OpenAI configuration.
/// TODO: allow overriding endpoint.
/// </summary>
public sealed class OpenAIConfig : IBackendConfig
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
    /// An identifier used to map semantic functions to backend,
    /// decoupling prompts configurations from the actual model used.
    /// </summary>
    public string Label { get; set; }

    /// <summary>
    /// Creates a new OpenAIConfig with supplied values.
    /// </summary>
    /// <param name="label">An identifier used to map semantic functions to backend,
    /// decoupling prompts configurations from the actual model used.</param>
    /// <param name="modelId">OpenAI model name, see https://platform.openai.com/docs/models</param>
    /// <param name="apiKey">OpenAI API key, see https://platform.openai.com/account/api-keys</param>
    /// <param name="orgId">OpenAI organization id. This is usually optional unless your account belongs to multiple organizations.</param>
    public OpenAIConfig(string label, string modelId, string apiKey, string? orgId)
    {
        Verify.NotEmpty(label, "The configuration label is empty");
        Verify.NotEmpty(modelId, "The model ID is empty");
        Verify.NotEmpty(apiKey, "The API key is empty");

        this.Label = label;
        this.ModelId = modelId;
        this.APIKey = apiKey;
        this.OrgId = orgId;
    }
}
