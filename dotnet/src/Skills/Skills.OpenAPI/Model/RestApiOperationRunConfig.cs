// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Model;

/// <summary>
/// Configuration for REST API operation run.
/// </summary>
internal class RestApiOperationRunConfig
{
    /// <summary>
    /// The dictionary of arguments to be passed to the operation.
    /// </summary>
    public IDictionary<string, string> Arguments { get; set; }

    /// <summary>
    /// Override for REST API operation server url.
    /// </summary>
    public Uri? ServerUrlOverride { get; set; }

    /// <summary>
    /// The URI of OpenApi document.
    /// </summary>
    public Uri? DocumentUri { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="RestApiOperationRunConfig"/> class.
    /// </summary>
    /// <param name="arguments">The dictionary of arguments to be passed to the operation.</param>
    public RestApiOperationRunConfig(IDictionary<string, string> arguments)
    {
        this.Arguments = arguments;
    }
}
