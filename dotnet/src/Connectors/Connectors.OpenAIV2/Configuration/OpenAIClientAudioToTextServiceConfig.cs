// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

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
