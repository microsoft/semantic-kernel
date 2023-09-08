// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Model;

/// <summary>
/// Options for REST API operation run.
/// </summary>
internal class RestApiOperationRunOptions
{
    /// <summary>
    /// Override for REST API operation server URL.
    /// </summary>
    public Uri? ServerUrlOverride { get; set; }

    /// <summary>
    /// The URL of REST API host.
    /// </summary>
    public Uri? ApiHostUrl { get; set; }
}
