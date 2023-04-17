// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel.Connectors.WebApi.Rest.Model;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Skills.OpenAPI.Model;

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
        parameters.Add(new RestApiOperationParameter(RestApiOperation.ServerUrlArgumentName, "string", false, RestApiOperationParameterLocation.Path,
            RestApiOperationParameterStyle.Simple, defaultValue: operation.ServerUrl));

        //Add Payload properties.
        parameters.AddRange(CreateParametersFromPayloadProperties(operation.Payload));

        //Create a property alternative name without special symbols that are not supported by SK template language.
        foreach (var parameter in parameters)
        {
            parameter.AlternativeName = Regex.Replace(parameter.Name, @"[^0-9A-Za-z_]+", "_");
        }

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

        IList<RestApiOperationParameter> ConvertLeafProperties(RestApiOperationPayloadProperty property)
        {
            var parameters = new List<RestApiOperationParameter>();

            if (!property.Properties.Any()) //It's a leaf property
            {
                parameters.Add(new RestApiOperationParameter(property.Name, property.Type, property.IsRequired, RestApiOperationParameterLocation.Body,
                    RestApiOperationParameterStyle.Simple, description: property.Description));
            }

            foreach (var childProperty in property.Properties)
            {
                parameters.AddRange(ConvertLeafProperties(childProperty));
            }

            return parameters;
        }

        var result = new List<RestApiOperationParameter>();

        foreach (var property in payload.Properties)
        {
            result.AddRange(ConvertLeafProperties(property));
        }

        return result;
    }
}
