// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Skills.OpenAPI.Model;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Builders.Query;

/// <summary>
/// A serializer for REST API operation query string parameters.
/// </summary>
internal interface IQueryStringParameterSerializer
{
    /// <summary>
    /// Serializes a REST API operation query string parameter.
    /// </summary>
    /// <param name="parameter">The REST API operation parameter to serialize.</param>
    /// <param name="argument">The parameter argument.</param>
    /// <returns>The serialized query string parameter.</returns>
    string Serialize(RestApiOperationParameter parameter, string argument);
}
