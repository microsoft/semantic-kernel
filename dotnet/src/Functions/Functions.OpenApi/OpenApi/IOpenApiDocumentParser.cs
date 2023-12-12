// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Interface for OpenAPI document parser classes.
/// </summary>
internal interface IOpenApiDocumentParser
{
    /// <summary>
    /// Parses OpenAPI document.
    /// </summary>
    /// <param name="stream">Stream containing OpenAPI document to parse.</param>
    /// <param name="ignoreNonCompliantErrors">Flag indicating whether to ignore non-compliant errors.
    /// If set to true, the parser will not throw exceptions for non-compliant documents.
    /// Please note that enabling this option may result in incomplete or inaccurate parsing results.</param>
    /// <param name="operationsToExclude">Optional list of operations not to import, e.g. in case they are not supported</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>List of rest operations.</returns>
    Task<IList<RestApiOperation>> ParseAsync(
        Stream stream,
        bool ignoreNonCompliantErrors = false,
        IList<string>? operationsToExclude = null,
        CancellationToken cancellationToken = default);
}
