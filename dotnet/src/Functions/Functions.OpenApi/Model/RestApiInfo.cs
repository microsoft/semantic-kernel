// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// The REST API information.
/// </summary>
public sealed class RestApiInfo
{
    /// <summary>
    /// The title of the application.
    /// </summary>
    public string? Title { get; init; }

    /// <summary>
    /// A short description of the application.
    /// </summary>
    public string? Description { get; init; }

    /// <summary>
    /// The version of the OpenAPI document.
    /// </summary>
    public string? Version { get; init; }

    /// <summary>
    /// Creates a new instance of the <see cref="RestApiInfo"/> class.
    /// </summary>
    internal RestApiInfo()
    {
    }
}
