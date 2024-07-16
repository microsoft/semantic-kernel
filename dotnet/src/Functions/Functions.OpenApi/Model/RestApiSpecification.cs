// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// The REST API specification.
/// </summary>
internal sealed class RestApiSpecification
{
    /// <summary>
    /// The REST API information.
    /// </summary>
    public RestApiInfo Info { get; private set; }

    /// <summary>
    /// The REST API operations.
    /// </summary>
    public IList<RestApiOperation> Operations { get; private set; }

    /// <summary>
    /// Construct an instance of <see cref="RestApiSpecification"/>
    /// </summary>
    /// <param name="info">REST API information.</param>
    /// <param name="operations">REST API operations.</param>
    public RestApiSpecification(RestApiInfo info, IList<RestApiOperation> operations)
    {
        this.Info = info;
        this.Operations = operations;
    }
}
