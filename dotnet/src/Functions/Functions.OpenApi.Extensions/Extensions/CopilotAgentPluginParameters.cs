// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;

/// <summary>
/// Copilot Agent Plugin parameters.
/// </summary>
public sealed class CopilotAgentPluginParameters
{
    /// <summary>
    /// Gets the HTTP client to be used in plugin initialization phase.
    /// </summary>
    public HttpClient? HttpClient { get; init; }

    /// <summary>
    /// Gets the user agent to be used in plugin initialization phase.
    /// </summary>
    public string? UserAgent { get; init; }

    /// <summary>
    /// A map of function execution parameters, where the key is the api dependency key from api manifest
    /// and the value is OpenApiFunctionExecutionParameters specific to that dependency.
    /// </summary>
    public Dictionary<string, OpenApiFunctionExecutionParameters>? FunctionExecutionParameters { get; init; }
}
