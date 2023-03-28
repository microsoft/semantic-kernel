// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Model;

/// <summary>
/// The Rest parameter location.
/// </summary>
internal enum RestParameterType
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

    /// <summary>
    /// Override parameter.
    /// </summary>
    Override,
}
