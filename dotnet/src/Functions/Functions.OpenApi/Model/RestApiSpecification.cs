// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// REST API specification.
/// </summary>
[Experimental("SKEXP0040")]
public sealed class RestApiSpecification
{
    /// <summary>
    /// The REST API information.
    /// </summary>
    public RestApiInfo Info { get; private set; }

    /// <summary>
    /// The REST API security requirements.
    /// </summary>
    public List<RestApiSecurityRequirement>? SecurityRequirements { get; private set; }

    /// <summary>
    /// The REST API operations.
    /// </summary>
    public IList<RestApiOperation> Operations { get; private set; }

    /// <summary>
    /// Construct an instance of <see cref="RestApiSpecification"/>
    /// </summary>
    /// <param name="info">REST API information.</param>
    /// <param name="securityRequirements">REST API security requirements.</param>
    /// <param name="operations">REST API operations.</param>
    internal RestApiSpecification(RestApiInfo info, List<RestApiSecurityRequirement>? securityRequirements, IList<RestApiOperation> operations)
    {
        this.Info = info;
        this.SecurityRequirements = securityRequirements;
        this.Operations = operations;
    }
}
