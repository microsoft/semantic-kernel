// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Model;

/// <summary>
/// Options for REST API operation run.
/// </summary>
internal class RestApiOperationRunOptions
{
    /// <summary>
    /// Override for REST API operation server url.
    /// </summary>
    public Uri? ServerUrlOverride { get; set; }

    /// <summary>
    /// The URI of OpenApi document.
    /// </summary>
    public Uri? DocumentUri { get; set; }
}
