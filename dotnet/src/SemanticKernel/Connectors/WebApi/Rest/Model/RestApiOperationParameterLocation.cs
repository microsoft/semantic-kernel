// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.WebApi.Rest.Model;

/// <summary>
/// The REST API operation parameter location.
/// </summary>
internal enum RestApiOperationParameterLocation
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
