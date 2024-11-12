// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// REST API parameter location.
/// </summary>
[Experimental("SKEXP0040")]
public enum RestApiParameterLocation
{
    /// <summary>
    /// Query parameter.
    /// </summary>
    Query,

    /// <summary>
    /// Header parameter.
    /// </summary>
    Header,

    /// <summary>
    /// Path parameter.
    /// </summary>
    Path,

    /// <summary>
    /// Cookie parameter.
    /// </summary>
    Cookie,

    /// <summary>
    /// Body parameter.
    /// </summary>
    Body,
}
