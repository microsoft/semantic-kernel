// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.OpenApi;

/// <summary>
/// Interface for OpenApi document parser classes.
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
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>List of rest operations.</returns>
    [RequiresUnreferencedCode("Implementation may use SharpYaml.Serialization.Serializer.Deserialize to parse YAML.")]
    [RequiresDynamicCode("Implementation may use SharpYaml to parse unknown types and JsonSerializer to serialize instances of those unknown types")]
    Task<IList<RestApiOperation>> ParseAsync(Stream stream, bool ignoreNonCompliantErrors = false, CancellationToken cancellationToken = default);
}
