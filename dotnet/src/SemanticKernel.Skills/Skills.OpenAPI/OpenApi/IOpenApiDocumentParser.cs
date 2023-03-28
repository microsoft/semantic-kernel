// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.OpenApi;

/// <summary>
/// Interface for OpenApi document classes.
/// </summary>
internal interface IOpenApiDocumentParser
{
    /// <summary>
    /// Parses OpenAPI document.
    /// </summary>
    /// <param name="stream">Stream containing OpenAPI document to parse.</param>
    /// <returns>List of rest operations.</returns>
    IList<RestApiOperation> Parse(Stream stream);
}
