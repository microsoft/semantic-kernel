// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Extensions;

/// <summary>
/// Class for extensions methods for the <see cref="RestApiOperation"/> class.
/// </summary>
internal static class RestApiOperationExtensions
{
    /// <summary>
    /// Returns list of REST API operation parameters.
    /// </summary>
    /// <returns>The list of parameters.</returns>
    public static IReadOnlyList<RestApiOperationParameter> GetParameters(this RestApiOperation operation)
    {
        var parameters = new List<RestApiOperationParameter>(operation.Parameters);

        //Register "server-url" as a parameter so that it's possible to override it if needed.
        parameters.Add(new RestApiOperationParameter(RestApiOperation.ServerUrlArgumentName, false, RestApiOperationParameterType.Path, operation.ServerUrl));

        //Add Payload properties.
        parameters.AddRange(CreateParametersFromPayloadProperties(operation.Payload));

        return parameters;
    }

    /// <summary>
    /// Creates parameters from REST API operation payload properties.
    /// </summary>
    /// <param name="payload">REST API operation payload.</param>
    /// <returns>The list of parameters.</returns>
    private static IEnumerable<RestApiOperationParameter> CreateParametersFromPayloadProperties(RestApiOperationPayload? payload)
    {
        if (payload == null)
        {
            return Enumerable.Empty<RestApiOperationParameter>();
        }

        IList<RestApiOperationParameter> ConverLeafProperties(RestApiOperationPayloadProperty property)
        {
            var parameters = new List<RestApiOperationParameter>();

            if (!property.Properties.Any()) //It's a leaf property
            {
                parameters.Add(new RestApiOperationParameter(property.Name, property.IsRequired, RestApiOperationParameterType.Body, null, property.Description));
            }

            foreach (var childProperty in property.Properties)
            {
                parameters.AddRange(ConverLeafProperties(childProperty));
            }

            return parameters;
        }

        var result = new List<RestApiOperationParameter>();

        foreach (var property in payload.Properties)
        {
            result.AddRange(ConverLeafProperties(property));
        }

        return result;
    }
}
