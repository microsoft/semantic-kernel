// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI specialized client text to image configuration
/// </summary>
public class OpenAITextToImageServiceConfig : BaseServiceConfig
{
    /// <summary>
    /// The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; init; }
}

/// <summary>
/// OpenAI specialized client file service configuration
/// </summary>
public class OpenAIFileServiceConfig : BaseServiceConfig
{
    /// <summary>
    /// The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; init; }
}

/// <summary>
/// OpenAI specializedd file service configuration
/// </summary>
public class OpenAIClientFileServiceConfig : OpenAIFileServiceConfig
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

    /// <summary>
    /// The API version to target.
    /// </summary>
    public string? Version { get; init; }
}
