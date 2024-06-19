// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI client specialized chat completion options.
/// </summary>
/// <param name="modelId">Model name.</param>
public class OpenAIClientChatCompletionConfig : OpenAIChatCompletionConfig
{
    /// <summary>
    /// OpenAI Organization Id (usually optional).
    /// </summary>
    public string? OrganizationId { get; init; }

    /// <summary>
    /// OpenAI API Key.
    /// </summary>
    public string? ApiKey { get; init; }

    /// <summary>
    /// A non-default OpenAI compatible API endpoint.
    /// </summary>
    public Uri? Endpoint { get; init; }
}
