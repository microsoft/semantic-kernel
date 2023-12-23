#region HEADER
// Copyright (c) Microsoft. All rights reserved.
#endregion

using System;

namespace Microsoft.SemanticKernel.Connectors.Gemini;

/// <summary>
/// Provides a collection of endpoints for the Gemini API.
/// </summary>
internal static class GeminiEndpoints
{
    /// <summary>
    /// Gets the base endpoint for the Gemini API.
    /// </summary>
    public static Uri BaseEndpoint { get; } = new("https://generativelanguage.googleapis.com/v1beta/");

    /// <summary>
    /// Gets the endpoint URI for accessing the models in the Gemini API.
    /// </summary>
    public static Uri ModelsEndpoint { get; } = new(BaseEndpoint, "models/");

    public static Uri GetGenerateContentEndpoint(string modelId, string apiKey)
        => new($"{ModelsEndpoint.AbsoluteUri}{modelId}:generateContent?key={apiKey}");

    public static Uri GetStreamGenerateContentEndpoint(string modelId, string apiKey)
        => new($"{ModelsEndpoint.AbsoluteUri}{modelId}:streamGenerateContent?key={apiKey}");
}
