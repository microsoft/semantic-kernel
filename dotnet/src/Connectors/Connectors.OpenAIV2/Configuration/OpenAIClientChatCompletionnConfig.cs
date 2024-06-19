// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI client specialized chat completion options.
/// </summary>
/// <param name="modelId">Model name.</param>
public class OpenAIClientChatCompletionnConfig(string modelId) : OpenAIChatCompletionConfig(modelId)
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

/// <summary>
/// OpenAI specialized client audio to text configuration
/// </summary>
public class OpenAIClientAudioToTextServiceConfig : OpenAIAudioToTextServiceConfig
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

/// <summary>
/// OpenAI specialized audio to text configuration
/// </summary>
public class OpenAIAudioToTextServiceConfig : BaseServiceConfig
{
    /// <summary>
    /// The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; init; }
}
